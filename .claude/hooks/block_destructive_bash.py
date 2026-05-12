#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
HOOK_EVENT_NAME = "PreToolUse"
SHELL_SEPARATORS = {";", "&&", "||", "|", "(", ")"}
GIT_OPTIONS_WITH_VALUE = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--config-env",
    "--exec-path",
}


def tokenize_command(command: str) -> list[str]:
    """Return shell-like tokens while keeping command separators visible."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return command.split()


def split_shell_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def is_assignment(token: str) -> bool:
    return re.match(r"^[A-Za-z_][A-Za-z0-9_]*=.*$", token) is not None


def command_word(segment: list[str]) -> tuple[str | None, list[str]]:
    index = 0
    while index < len(segment):
        word = segment[index]
        if is_assignment(word):
            index += 1
            continue
        if word in {"command", "builtin", "time"}:
            index += 1
            continue
        if word == "sudo":
            index += 1
            while index < len(segment) and segment[index].startswith("-"):
                option = segment[index]
                index += 1
                if option in {"-u", "--user", "-g", "--group", "-h", "--host"}:
                    index += 1
            continue
        if word == "env":
            index += 1
            while index < len(segment):
                env_word = segment[index]
                if env_word.startswith("-") or is_assignment(env_word):
                    index += 1
                    continue
                break
            continue
        return word, segment[index + 1 :]
    return None, []


def rm_uses_recursive_force(args: list[str]) -> bool:
    recursive = False
    force = False
    for arg in args:
        if arg == "--":
            break
        if arg in {"--recursive", "--dir"}:
            recursive = True
        elif arg == "--force":
            force = True
        elif arg.startswith("-") and not arg.startswith("--"):
            flags = arg[1:]
            recursive = recursive or "r" in flags or "R" in flags
            force = force or "f" in flags
    return recursive and force


def skip_git_global_option(args: list[str], index: int) -> int:
    option = args[index]
    if option in GIT_OPTIONS_WITH_VALUE:
        return index + 2
    for prefix in ("--git-dir=", "--work-tree=", "--namespace=", "--config-env=", "--exec-path="):
        if option.startswith(prefix):
            return index + 1
    return index + 1


def git_push_uses_force(args: list[str]) -> bool:
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("-"):
            index = skip_git_global_option(args, index)
            continue
        break

    if index >= len(args) or args[index] != "push":
        return False

    for arg in args[index + 1 :]:
        if arg in {"-f", "--force"} or arg.startswith("--force-with-lease"):
            return True
        if arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]:
            return True
    return False


def nested_shell_command(executable: str, args: list[str]) -> str | None:
    if Path(executable).name not in {"bash", "sh", "zsh"}:
        return None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("-") and "c" in arg and index + 1 < len(args):
            return args[index + 1]
        index += 1
    return None


def sql_statement_from(command: str, start: int) -> str:
    tail = command[start:]
    end_match = re.search(r";|\n|&&|\|\|", tail)
    if not end_match:
        return tail
    return tail[: end_match.start()]


def sql_findings(command: str) -> list[str]:
    findings: list[str] = []
    if re.search(r"\bdrop\s+table\b", command, re.IGNORECASE):
        findings.append("DROP TABLE statement")
    if re.search(r"\btruncate\b", command, re.IGNORECASE):
        findings.append("TRUNCATE statement")
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = sql_statement_from(command, match.start())
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            findings.append("DELETE FROM statement without WHERE clause")
            break
    return findings


def detect_dangerous_command(command: str) -> list[str]:
    findings: list[str] = []

    for segment in split_shell_segments(tokenize_command(command)):
        executable, args = command_word(segment)
        if not executable:
            continue

        nested = nested_shell_command(executable, args)
        if nested is not None:
            findings.extend(detect_dangerous_command(nested))

        executable_name = Path(executable).name
        if executable_name == "rm" and rm_uses_recursive_force(args):
            findings.append("rm command with both recursive and force flags")
        elif executable_name == "git" and git_push_uses_force(args):
            findings.append("git push with force flag")

    findings.extend(sql_findings(command))

    deduped: list[str] = []
    for finding in findings:
        if finding not in deduped:
            deduped.append(finding)
    return deduped


def project_path(event: dict[str, Any]) -> str:
    return (
        str(event.get("cwd") or event.get("workspace") or os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())
    )


def write_block_log(command: str, reasons: list[str], path: str, log_path: Path = LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": path,
        "attempted_command": command,
        "reasons": reasons,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def denial_output(reasons: list[str]) -> dict[str, Any]:
    reason_text = "; ".join(reasons)
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command before execution: "
                f"{reason_text}. Rewrite the command to avoid irreversible changes."
            ),
        }
    }


def process_event(event: dict[str, Any], log_path: Path = LOG_PATH) -> dict[str, Any] | None:
    if event.get("tool_name") != "Bash":
        return None

    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    reasons = detect_dangerous_command(command)
    if not reasons:
        return None

    write_block_log(command, reasons, project_path(event), log_path)
    return denial_output(reasons)


def hook_config(script_path: Path) -> dict[str, Any]:
    return {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": sys.executable,
                "args": [str(script_path)],
            }
        ],
    }


def install_user_hook() -> int:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    source = Path(__file__).resolve()
    target = hooks_dir / source.name
    if source != target:
        shutil.copy2(source, target)

    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Cannot update invalid JSON in {settings_path}: {exc}", file=sys.stderr)
            return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    config = hook_config(target)
    if not any(existing == config for existing in pre_tool_use):
        pre_tool_use.append(config)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed PreToolUse hook in {settings_path}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-user", action="store_true", help="Install this hook in ~/.claude/settings.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.install_user:
        return install_user_hook()

    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    output = process_event(event)
    if output:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
