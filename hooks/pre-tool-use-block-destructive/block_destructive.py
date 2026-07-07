#!/usr/bin/env python3
"""PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


DROP_DDL = re.compile(r"(?is)\bdrop\s+(table|database|schema|index|view|function|procedure)\b")
DELETE_FROM = re.compile(r"(?is)\bdelete\s+from\b")
UPDATE_SET = re.compile(r"(?is)\bupdate\s+[\w.]+\s+set\b")
ALTER_TABLE_DROP = re.compile(r"(?is)\balter\s+table\b.*\bdrop\b")
TRUNCATE = re.compile(r"(?is)\btruncate(?:\s+table)?\s+[a-z_][\w.]*")
WHERE = re.compile(r"(?is)\bwhere\b")
MKFS = re.compile(r"(?is)(?:^|[\s;&|])(?:mkfs(?:\.\w+)?|mkswap)(?:\s|$)")
DD_TO_BLOCK_DEVICE = re.compile(
    r"(?is)(?:^|[\s;&|])dd\s+[^\n;&|]*\bof=/dev/(sd|hd|vd|xvd|nvme|disk)"
)
REDIRECT_TO_BLOCK_DEVICE = re.compile(
    r"(?is)(?:^|[\s;&|])(?:>|1>|2>)\s*/dev/(sd|hd|vd|xvd|nvme|disk)"
)
CHMOD_777_ROOT = re.compile(
    r"(?is)(?:^|[\s;&|])chmod\s+(?:-[\w]*R[\w]*\s+|--recursive\s+)?(?:777|666)\s+/"
)
WIPEFS = re.compile(r"(?is)(?:^|[\s;&|])wipefs(?:\s|$)")
FORK_BOMB = re.compile(r"(?is):\s*\(\s*\)\s*\{.*:\s*\|.*:.*&.*\}")
READ_ONLY_TEXT_COMMANDS = {
    "ag",
    "awk",
    "cat",
    "echo",
    "grep",
    "head",
    "less",
    "more",
    "printf",
    "rg",
    "sed",
    "tail",
    "tee",
}
SQL_CLIENT_COMMANDS = {"mariadb", "mysql", "mysqladmin", "psql", "sqlite3", "sqlcmd"}
GIT_FORCE_CONFIG_FALSE_VALUES = {"false", "0", "no", "off", "n"}
REMOTE_SHELLS = {"bash", "sh"}
REMOTE_DOWNLOADERS = {"curl", "wget"}
SHELL_C_COMMANDS = {"bash", "dash", "fish", "ksh", "sh", "zsh"}
SHELL_DOLLAR_C_COMMAND = re.compile(
    r"""(?is)\b(?:bash|dash|fish|ksh|sh|zsh)\b(?:\s+(?:--[\w-]+(?:=\S+)?|-[A-Za-z]+))*\s+-[A-Za-z]*c\b\s+\$(?P<quote>['"])(?P<body>(?:\\.|(?!\1).)*)\1"""
)
INTERPRETER_INLINE_COMMANDS = {"node", "perl", "python", "python3", "ruby"}
INTERPRETER_EXECUTION_HINT = re.compile(
    r"(?is)\b(?:child_process|exec(?:file|sync|vp|ve|le)?|os\.system|popen|spawn|subprocess|system)\b"
)
STRING_LITERAL = re.compile(r"""(?sx)(['"])((?:\\.|(?!\1).)*)\1""")
EVASION_SEPARATORS = "\x00\u115f\u1160\u2800\u3164\uffa0"
SUDO_OPTIONS_WITH_VALUES = {
    "-C",
    "-D",
    "-g",
    "-h",
    "-p",
    "-u",
    "--chdir",
    "--close-from",
    "--group",
    "--host",
    "--prompt",
    "--user",
}
DOAS_OPTIONS_WITH_VALUES = {"-u", "-C", "-L"}
RUNUSER_OPTIONS_WITH_VALUES = {
    "-c",
    "-g",
    "-G",
    "-s",
    "-u",
    "--command",
    "--group",
    "--login",
    "--shell",
    "--supp-group",
    "--user",
}
ENV_OPTIONS_WITH_VALUES = {
    "-C",
    "-S",
    "-u",
    "--chdir",
    "--split-string",
    "--unset",
}
CONTAINER_EXEC_COMMANDS = {"docker", "kubectl", "nerdctl", "podman"}
CONTAINER_EXEC_OPTIONS_WITH_VALUES = {
    "-c",
    "-n",
    "-u",
    "-w",
    "--container",
    "--context",
    "--namespace",
    "--user",
    "--workdir",
}
DANGEROUS_FIND_DELETE_ROOTS = {"/", "~", "$HOME", "${HOME}"}


def find_block_reason(command: str) -> str | None:
    command = normalize_command(command)

    if has_rm_recursive_force(command):
        return "Recursive forced deletion is blocked. Matched pattern: rm -rf."

    if has_forced_git_push(command):
        return "Force-pushing is blocked. Matched pattern: git push --force."

    if has_destructive_git_history_command(command):
        return "Destructive Git history cleanup is blocked. Matched pattern: git reset --hard/git clean -fd."

    if has_destructive_find_delete(command):
        return "Broad find deletion is blocked. Matched pattern: find / -delete or find $HOME -delete."

    if has_remote_shell_pipe(command):
        return "Remote script execution is blocked. Matched pattern: curl|bash or wget|sh."

    if has_destructive_interpreter_inline(command):
        return "Destructive inline interpreter execution is blocked. Matched pattern: python/node/ruby/perl -c/-e."

    if has_destructive_drop(command):
        return "Destructive DROP statement is blocked. Matched pattern: DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW."

    if has_sql_truncate(command):
        return "TRUNCATE statements are blocked. Matched pattern: TRUNCATE."

    if has_block_device_write(command):
        return "Direct writes to block devices are blocked. Matched pattern: mkfs/dd/> /dev."

    if WIPEFS.search(command):
        return "Disk signature wiping is blocked. Matched pattern: wipefs."

    if FORK_BOMB.search(command):
        return "Shell fork bombs are blocked. Matched pattern: :(){ :|:& };:."

    if CHMOD_777_ROOT.search(command):
        return "Recursive permissive chmod on root paths is blocked. Matched pattern: chmod 777 /."

    sql_reason = destructive_sql_statement_reason(command)
    if sql_reason:
        return sql_reason

    return None


def normalize_command(command: str) -> str:
    if not any(char in command for char in EVASION_SEPARATORS):
        return command

    space_translation = str.maketrans({char: " " for char in EVASION_SEPARATORS})
    remove_translation = str.maketrans("", "", EVASION_SEPARATORS)
    return command.translate(space_translation) + "\n" + command.translate(remove_translation)


def has_rm_recursive_force(command: str) -> bool:
    for words in shell_commands(command):
        for words in executable_command_positions(words):
            if not words or command_name(words[0]) != "rm":
                continue

            has_recursive = False
            has_force = False
            for option in words[1:]:
                if option == "--":
                    continue
                if not option.startswith("-") or option == "-":
                    break

                if option == "--recursive" or option.startswith("--recursive="):
                    has_recursive = True
                elif option == "--force" or option.startswith("--force="):
                    has_force = True
                elif option.startswith("--"):
                    continue
                else:
                    flags = option.lstrip("-")
                    has_recursive = has_recursive or "r" in flags.lower()
                    has_force = has_force or "f" in flags

                if has_recursive and has_force:
                    return True

    return False


def executable_command_positions(words: list[str]) -> list[list[str]]:
    commands = []
    segment = []
    for word in words:
        if word == "|":
            commands.append(strip_command_wrappers(segment))
            segment = []
            continue
        segment.append(word)
    commands.append(strip_command_wrappers(segment))
    return [command for command in commands if command]


def has_forced_git_push(command: str) -> bool:
    for words in shell_commands(command):
        words = strip_command_wrappers(words)
        for index, word in enumerate(words):
            if command_name(word) != "git":
                continue

            git_args = words[index + 1 :]
            push_index = next(
                (i for i, arg in enumerate(git_args) if arg.lower() == "push"),
                None,
            )
            if push_index is None:
                continue

            push_args = [arg.lower() for arg in git_args[push_index + 1 :]]
            if git_force_config_enabled(git_args[:push_index]):
                return True
            if any(
                arg in {"--force", "--force-with-lease", "-f"}
                or arg.startswith("--force-with-lease=")
                or arg.startswith("--force=")
                or arg.startswith("+")
                for arg in push_args
            ):
                return True

    return False


def git_force_config_enabled(args: list[str]) -> bool:
    for index, arg in enumerate(args):
        config = None
        if arg == "-c" and index + 1 < len(args):
            config = args[index + 1]
        elif arg.startswith("-c") and len(arg) > 2:
            config = arg[2:].lstrip()

        if not config:
            continue

        key, has_value, value = config.partition("=")
        if key.lower() != "push.force":
            continue

        normalized_value = value.strip().strip("'\"").lower()
        if not has_value or normalized_value not in GIT_FORCE_CONFIG_FALSE_VALUES:
            return True

    return False


def has_destructive_git_history_command(command: str) -> bool:
    for words in shell_commands(command):
        words = strip_command_wrappers(words)
        for index, word in enumerate(words):
            if command_name(word) != "git":
                continue

            git_args = [arg.lower() for arg in words[index + 1 :]]
            reset_index = next(
                (i for i, arg in enumerate(git_args) if arg == "reset"),
                None,
            )
            if reset_index is not None and "--hard" in git_args[reset_index + 1 :]:
                return True

            clean_index = next(
                (i for i, arg in enumerate(git_args) if arg == "clean"),
                None,
            )
            if clean_index is None:
                continue

            clean_args = git_args[clean_index + 1 :]
            has_force = False
            has_directory_or_ignored = False
            is_dry_run = False
            for arg in clean_args:
                if arg in {"--force", "-f"}:
                    has_force = True
                elif arg in {"-d", "--directories", "-x", "-X"}:
                    has_directory_or_ignored = True
                elif arg in {"-n", "--dry-run"}:
                    is_dry_run = True
                elif arg.startswith("-") and not arg.startswith("--"):
                    flags = arg.lstrip("-")
                    has_force = has_force or "f" in flags
                    has_directory_or_ignored = has_directory_or_ignored or any(
                        flag in flags for flag in ("d", "x", "X")
                    )
                    is_dry_run = is_dry_run or "n" in flags

            if has_force and has_directory_or_ignored and not is_dry_run:
                return True

    return False


def has_destructive_find_delete(command: str) -> bool:
    for words in shell_commands(command):
        words = strip_command_wrappers(words)
        if not words or command_name(words[0]) != "find" or "-delete" not in words:
            continue

        roots = []
        for word in words[1:]:
            if word.startswith("-"):
                break
            roots.append(word)

        if any(root in DANGEROUS_FIND_DELETE_ROOTS for root in roots):
            return True

    return False


def strip_command_wrappers(words: list[str]) -> list[str]:
    result = list(words)
    while result:
        head = command_name(result[0])
        if head == "sudo":
            result = strip_option_prefix(result[1:], SUDO_OPTIONS_WITH_VALUES)
            continue
        if head == "command":
            result = strip_option_prefix(result[1:], set())
            continue
        if head == "env":
            result = strip_env_prefix(result[1:])
            continue
        if head == "doas":
            result = strip_option_prefix(result[1:], DOAS_OPTIONS_WITH_VALUES)
            continue
        if head == "pkexec":
            result = strip_option_prefix(result[1:], set())
            continue
        if head == "runuser":
            result = strip_runuser_prefix(result[1:])
            continue
        container_inner = container_exec_inner_command(result)
        if container_inner is not None:
            result = container_inner
            continue
        break
    return result


def strip_runuser_prefix(words: list[str]) -> list[str]:
    result = list(words)
    while result:
        token = result[0]
        if token == "--":
            return result[1:]

        option_name, has_inline_value, inline_value = token.partition("=")
        if option_name in {"-c", "--command"}:
            if has_inline_value:
                return shell_words(inline_value)
            if len(result) > 1:
                return shell_words(result[1])
            return []

        if option_name in RUNUSER_OPTIONS_WITH_VALUES:
            result = result[1:] if has_inline_value else result[2:]
            continue

        if len(token) > 2 and token[:2] in RUNUSER_OPTIONS_WITH_VALUES:
            result = result[1:]
            continue

        if token.startswith("-") and token != "-":
            result = result[1:]
            continue

        return result
    return result


def strip_env_prefix(words: list[str]) -> list[str]:
    result = strip_option_prefix(words, ENV_OPTIONS_WITH_VALUES)
    while result:
        token = result[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            result = result[1:]
            continue
        return result
    return result


def strip_option_prefix(words: list[str], options_with_values: set[str]) -> list[str]:
    result = list(words)
    while result:
        token = result[0]
        if token == "--":
            return result[1:]
        if not token.startswith("-") or token == "-":
            return result

        option_name, has_inline_value, _ = token.partition("=")
        if option_name in options_with_values:
            result = result[1:] if has_inline_value else result[2:]
            continue

        if len(token) > 2 and token[:2] in options_with_values:
            result = result[1:]
            continue

        result = result[1:]
    return result


def container_exec_inner_command(words: list[str]) -> list[str] | None:
    if not words or command_name(words[0]) not in CONTAINER_EXEC_COMMANDS:
        return None

    if command_name(words[0]) == "docker" and len(words) > 2 and words[1] == "compose":
        if words[2] != "exec":
            return None
        tail = words[3:]
    elif len(words) > 1 and words[1] == "exec":
        tail = words[2:]
    else:
        return None

    tail = strip_container_exec_options(tail)
    if not tail:
        return None

    inner = tail[1:]
    if inner and inner[0] == "--":
        inner = inner[1:]
    return inner or None


def strip_container_exec_options(words: list[str]) -> list[str]:
    result = list(words)
    while result:
        option = result[0]
        if option == "--":
            return result[1:]
        if not option.startswith("-") or option == "-":
            return result
        if option.split("=", 1)[0] in CONTAINER_EXEC_OPTIONS_WITH_VALUES:
            result = result[2:] if "=" not in option and len(result) > 1 else result[1:]
            continue
        result = result[1:]
    return result


def has_block_device_write(command: str) -> bool:
    return bool(
        MKFS.search(command)
        or DD_TO_BLOCK_DEVICE.search(command)
        or REDIRECT_TO_BLOCK_DEVICE.search(command)
    )


def has_remote_shell_pipe(command: str) -> bool:
    for words in shell_commands(command):
        for index, word in enumerate(words):
            if command_name(word) not in REMOTE_DOWNLOADERS:
                continue
            try:
                pipe_index = words.index("|", index + 1)
            except ValueError:
                continue
            shell_words_after_pipe = strip_command_wrappers(words[pipe_index + 1 :])
            if shell_words_after_pipe and command_name(shell_words_after_pipe[0]) in REMOTE_SHELLS:
                return True
    return False


def has_destructive_interpreter_inline(command: str) -> bool:
    for words in shell_commands(command):
        code = interpreter_inline_code(words)
        if not code or INTERPRETER_EXECUTION_HINT.search(code) is None:
            continue
        for literal in command_literals(code):
            if find_block_reason(literal):
                return True
    return False


def interpreter_inline_code(words: list[str]) -> str | None:
    words = strip_command_wrappers(words)
    if not words or command_name(words[0]) not in INTERPRETER_INLINE_COMMANDS:
        return None

    for index, word in enumerate(words[1:-1], start=1):
        if word in {"-c", "-e"}:
            return words[index + 1]
        if word.startswith("-") and len(word) > 2 and any(flag in word[1:] for flag in ("c", "e")):
            return words[index + 1]

    return None


def command_literals(code: str) -> list[str]:
    return [
        bytes(match.group(2), "utf-8").decode("unicode_escape")
        for match in STRING_LITERAL.finditer(code)
    ]


def has_destructive_drop(command: str) -> bool:
    for words in shell_commands(command):
        if is_read_only_search_command(words):
            continue
        if DROP_DDL.search(" ".join(words)):
            return True
    return False


def has_sql_truncate(command: str) -> bool:
    for words in shell_commands(command):
        if is_read_only_search_command(words):
            continue
        if words and command_name(words[0]) == "truncate" and len(words) > 1:
            if words[1].startswith("-"):
                continue
        if TRUNCATE.search(" ".join(words)):
            return True
    return False


def destructive_sql_statement_reason(command: str) -> str | None:
    for words in shell_commands(command):
        if is_read_only_search_command(words):
            continue
        segment = strip_sql_comments(" ".join(words))
        for statement in split_sql_statements(segment):
            if DELETE_FROM.search(statement) and not WHERE.search(statement):
                return "DELETE FROM without a WHERE clause is blocked. Matched pattern: DELETE FROM."
            if UPDATE_SET.search(statement) and not WHERE.search(statement):
                return "UPDATE without a WHERE clause is blocked. Matched pattern: UPDATE SET."
            if ALTER_TABLE_DROP.search(statement):
                return "ALTER TABLE DROP statements are blocked. Matched pattern: ALTER TABLE DROP."
    return None


def is_read_only_search_command(words: list[str]) -> bool:
    words = strip_command_wrappers(words)
    return bool(
        words
        and command_name(words[0]) in READ_ONLY_TEXT_COMMANDS
        and not has_sql_client_command(words)
    )


def has_sql_client_command(words: list[str]) -> bool:
    return any(command_name(word) in SQL_CLIENT_COMMANDS for word in words)


def shell_commands(command: str) -> list[list[str]]:
    commands = []
    for segment in split_shell_segments(command):
        if not segment.strip():
            continue

        words = shell_words(segment)
        commands.append(words)

        inner = shell_dollar_c_command(segment) or shell_c_command(words)
        if inner:
            commands.extend(shell_commands(inner))

    return commands


def split_shell_segments(command: str) -> list[str]:
    segments = []
    current = []
    in_single = False
    in_double = False
    escaped = False
    index = 0

    def flush() -> None:
        segment = "".join(current).strip()
        if segment:
            segments.append(segment)
        current.clear()

    while index < len(command):
        char = command[index]
        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue
        if char == "\\" and in_double:
            current.append(char)
            escaped = True
            index += 1
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            current.append(char)
            index += 1
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            current.append(char)
            index += 1
            continue
        if not in_single and not in_double:
            if command.startswith("&&", index) or command.startswith("||", index):
                flush()
                index += 2
                continue
            if char in {";", "\n"}:
                flush()
                index += 1
                continue
        current.append(char)
        index += 1

    flush()
    return segments


def shell_c_command(words: list[str]) -> str | None:
    words = strip_command_wrappers(words)
    if not words or command_name(words[0]) not in SHELL_C_COMMANDS:
        return None

    for index, word in enumerate(words[1:-1], start=1):
        if word == "-c" or (word.startswith("-") and "c" in word[1:]):
            return words[index + 1]

    return None


def shell_dollar_c_command(command: str) -> str | None:
    match = SHELL_DOLLAR_C_COMMAND.search(command)
    if not match:
        return None
    return decode_backslash_escapes(match.group("body"))


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def command_name(word: str) -> str:
    return Path(word).name.lower()


def decode_backslash_escapes(text: str) -> str:
    return bytes(text, "utf-8").decode("unicode_escape")


def split_sql_statements(command: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;\n]", command) if part.strip()]


def strip_sql_comments(statement: str) -> str:
    without_block_comments = re.sub(r"(?is)/\*.*?\*/", " ", statement)
    return "\n".join(
        re.sub(r"--.*$", "", line) for line in without_block_comments.splitlines()
    )


def hook_output(decision: str | None = None, reason: str | None = None) -> dict:
    if decision is None:
        return {"continue": True, "suppressOutput": True}

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def log_blocked_attempt(command: str, cwd: str, reason: str) -> None:
    log_dir = hooks_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def hooks_dir() -> Path:
    override = os.environ.get("CLAUDE_HOOKS_DIR")
    if override:
        return Path(override)

    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        return Path(config_dir) / "hooks"

    return Path.home() / ".claude" / "hooks"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                hook_output(
                    "deny",
                    f"Could not parse PreToolUse hook input as JSON: {exc}",
                )
            )
        )
        return 0

    if payload.get("tool_name") != "Bash":
        print(json.dumps(hook_output()))
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    cwd = payload.get("cwd") or os.getcwd()
    reason = find_block_reason(command)

    if reason is None:
        print(json.dumps(hook_output()))
        return 0

    log_blocked_attempt(command, cwd, reason)
    print(json.dumps(hook_output("deny", reason)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
