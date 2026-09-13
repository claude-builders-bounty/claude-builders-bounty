#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands.

Reads the PreToolUse event JSON from stdin, inspects the Bash command, and
either stays silent (the command continues through Claude Code's normal
permission flow) or prints a `permissionDecision: "deny"` object on stdout.

Blocked attempts are appended to ~/.claude/hooks/blocked.log as JSON lines.

Protocol: https://code.claude.com/docs/en/hooks

Usage:
    block_destructive_bash.py                 run as a hook (JSON on stdin)
    block_destructive_bash.py --install       register in ~/.claude/settings.json
    block_destructive_bash.py --uninstall     remove from ~/.claude/settings.json
    block_destructive_bash.py --check CMD     print the verdict for CMD
"""

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_EVENT = "PreToolUse"
SCRIPT_NAME = os.path.basename(os.path.abspath(__file__))
MAX_NESTING_DEPTH = 3
MAX_COMMAND_IN_MESSAGE = 500
MAX_COMMAND_IN_LOG = 4000

# `git push --force-with-lease` refuses to overwrite commits the local clone has
# not seen, so it is treated as the safe alternative. Set this to True to block
# it too.
BLOCK_FORCE_WITH_LEASE = False

# Programs that wrap another command instead of being the command themselves.
WRAPPERS = {
    "sudo", "doas", "env", "nice", "ionice", "nohup", "time", "timeout",
    "stdbuf", "command", "exec", "xargs", "setsid", "unbuffer",
}

# Programs that only read or print text. A command built solely from these
# cannot execute SQL or delete anything, so pattern matches inside their
# arguments are quotes, not actions: `grep -r "DROP TABLE" migrations/` is fine.
INERT_PROGRAMS = {
    "echo", "printf", "cat", "grep", "egrep", "fgrep", "rg", "ack", "head",
    "tail", "less", "more", "wc", "diff", "comm", "sort", "uniq", "cut", "nl",
    "column", "tee", "true",
}

SHELLS = {"sh", "bash", "zsh", "dash", "ksh", "ash", "fish"}

COMMAND_SEPARATORS = {"|", "||", "&&", ";", ";;", "&", "|&", "(", ")", "{", "}"}

DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
# Matches SQL `TRUNCATE` and coreutils `truncate`, but not names that merely
# contain the word, such as `npm run truncate-logs` or `truncate.py`.
TRUNCATE_RE = re.compile(r"(?<![\w-])truncate\b(?![-.])", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)

RULES = {
    "rm-rf": (
        "`rm -rf` deletes whole directory trees with no prompt and no undo.",
        "Delete specific paths without `-rf`, or ask the user to run it "
        "themselves if the recursive delete is really intended.",
    ),
    "git-force-push": (
        "`git push --force` overwrites remote history and can destroy commits "
        "other people rely on.",
        "Push normally, or use `git push --force-with-lease` so the push fails "
        "instead of discarding commits you have not fetched.",
    ),
    "sql-drop-table": (
        "`DROP TABLE` permanently removes a table and all of its rows.",
        "Run schema changes through a reviewed migration, or ask the user to "
        "apply it.",
    ),
    "sql-truncate": (
        "`TRUNCATE` empties a table (or file) and is not transactional on many "
        "databases, so the rows cannot be recovered.",
        "Delete a bounded set of rows with an explicit `WHERE` clause, or ask "
        "the user to run it.",
    ),
    "sql-delete-without-where": (
        "`DELETE FROM` without a `WHERE` clause removes every row in the table.",
        "Add a `WHERE` clause that selects only the rows you mean to delete.",
    ),
}


def tokenize(command):
    """Split a shell command into tokens, or return None if it cannot be parsed.

    Quotes are removed and operators such as `|` and `&&` become their own
    tokens, so the text inside `echo "rm -rf /"` is one harmless argument.
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def is_redirection(token):
    return ("<" in token or ">" in token) and all(
        char in "0123456789<>&-" for char in token
    )


def split_segments(tokens):
    """Group tokens into simple commands, dropping operators and redirections."""
    segments = []
    current = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue
        if token in COMMAND_SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        if is_redirection(token):
            skip_next = True
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def program_of(segment):
    """Best-effort name of the program a segment runs, ignoring wrappers."""
    for token in segment:
        base = os.path.basename(token)
        if base in WRAPPERS or token.startswith("-"):
            continue
        if "=" in token and not token.startswith(("/", "./")):
            continue
        return base
    return ""


def is_inert(segment):
    return program_of(segment) in INERT_PROGRAMS


def nested_commands(segments):
    """Command strings passed to a nested shell, e.g. `bash -c "..."`."""
    found = []
    for segment in segments:
        for index, token in enumerate(segment):
            base = os.path.basename(token)
            if base == "eval":
                rest = segment[index + 1:]
                if rest:
                    found.append(" ".join(rest))
                break
            if base in SHELLS:
                for offset in range(index + 1, len(segment)):
                    flag = segment[offset]
                    if flag.startswith("-") and "c" in flag.lstrip("-"):
                        if offset + 1 < len(segment):
                            found.append(segment[offset + 1])
                        break
                break
    return found


def rm_is_destructive(args):
    """True when an `rm` argument list carries both recursive and force flags."""
    recursive = force = False
    for arg in args:
        if arg == "--":
            break
        if arg.startswith("--"):
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
        elif arg.startswith("-") and len(arg) > 1:
            letters = arg[1:]
            if "r" in letters or "R" in letters:
                recursive = True
            if "f" in letters:
                force = True
    return recursive and force


def check_rm(segments):
    for segment in segments:
        if is_inert(segment):
            continue
        for index, token in enumerate(segment):
            if os.path.basename(token) == "rm" and rm_is_destructive(segment[index + 1:]):
                return "rm-rf"
    return None


def check_git_push(segments):
    for segment in segments:
        if is_inert(segment):
            continue
        for index, token in enumerate(segment):
            if os.path.basename(token) != "git" or "push" not in segment[index + 1:]:
                continue
            rest = segment[index + 1:]
            for arg in rest[rest.index("push") + 1:]:
                if arg.startswith(("--force-with-lease", "--force-if-includes")):
                    if BLOCK_FORCE_WITH_LEASE:
                        return "git-force-push"
                    continue
                if arg == "-f" or arg.startswith("--force"):
                    return "git-force-push"
                if arg.startswith("+") and ":" in arg:
                    return "git-force-push"
    return None


def delete_without_where(text):
    """True when any `DELETE FROM` statement in text has no `WHERE` clause."""
    for match in DELETE_FROM_RE.finditer(text):
        statement = text[match.start():]
        end = statement.find(";")
        if end != -1:
            statement = statement[:end]
        if not WHERE_RE.search(statement):
            return True
    return False


def check_sql(command, segments, tokenized):
    # SQL travels inside quotes (`psql -c "DROP TABLE users"`), so these rules
    # read the raw command text. Skip commands that only read or print text.
    if tokenized and segments and all(is_inert(segment) for segment in segments):
        return None
    if DROP_TABLE_RE.search(command):
        return "sql-drop-table"
    if TRUNCATE_RE.search(command):
        return "sql-truncate"
    if delete_without_where(command):
        return "sql-delete-without-where"
    return None


def check_untokenizable(command):
    """Pattern fallback for commands shlex cannot parse, e.g. unbalanced quotes."""
    for match in re.finditer(r"\brm\b((?:\s+-{1,2}[A-Za-z-]+)*)", command):
        if rm_is_destructive(match.group(1).split()):
            return "rm-rf"
    force_push = re.search(
        r"\bgit\b[^;|&]*\bpush\b[^;|&]*?"
        r"(--force(?!-with-lease|-if-includes)|(?<!\S)-f(?!\S))",
        command,
        re.IGNORECASE,
    )
    if force_push:
        return "git-force-push"
    return check_sql(command, [], tokenized=False)


def analyze(command, depth=0):
    """Return the id of the first rule the command violates, or None."""
    if not command or not command.strip():
        return None
    tokens = tokenize(command)
    if tokens is None:
        return check_untokenizable(command)
    segments = split_segments(tokens)
    for rule in (check_rm(segments), check_git_push(segments)):
        if rule:
            return rule
    rule = check_sql(command, segments, tokenized=True)
    if rule:
        return rule
    if depth < MAX_NESTING_DEPTH:
        for nested in nested_commands(segments):
            rule = analyze(nested, depth + 1)
            if rule:
                return rule
    return None


def truncate(text, limit):
    return text if len(text) <= limit else text[:limit] + " …(truncated)"


def log_file():
    return Path(os.path.expanduser("~")) / ".claude" / "hooks" / "blocked.log"


def log_blocked(rule, command, project_path, session_id):
    """Append one JSON line per blocked attempt. Never raises."""
    entry = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rule": rule,
        "command": truncate(command, MAX_COMMAND_IN_LOG),
        "project_path": project_path,
        "session_id": session_id,
    }
    try:
        path = log_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def denial_message(rule, command, logged=True):
    why, instead = RULES[rule]
    message = (
        "Blocked by the destructive-command hook (rule: {rule}).\n\n"
        "Command: {command}\n"
        "Why: {why}\n"
        "Instead: {instead}"
    ).format(
        rule=rule,
        command=truncate(command, MAX_COMMAND_IN_MESSAGE),
        why=why,
        instead=instead,
    )
    if logged:
        message += (
            "\n\nThis attempt was logged to ~/.claude/hooks/blocked.log. Do not "
            "retry the same command; if the user explicitly wants it, ask them "
            "to run it themselves."
        )
    return message


def run_hook():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
        # Not a payload this hook understands; let Claude Code proceed.
        return 0
    if not isinstance(event, dict):
        return 0
    if event.get("tool_name") not in ("Bash", "PowerShell"):
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str):
        return 0

    rule = analyze(command)
    if rule is None:
        # Silence means "no objection": the command still goes through Claude
        # Code's normal permission flow. Returning "allow" would skip it.
        return 0

    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()
    log_blocked(rule, command, project_path, event.get("session_id", ""))

    reason = denial_message(rule, command)
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": HOOK_EVENT,
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
            "systemMessage": "Blocked a destructive command ({rule}). See "
            "~/.claude/hooks/blocked.log".format(rule=rule),
        },
        sys.stdout,
    )
    return 0


def hook_command_string():
    """The command to register in settings.json for this script's location."""
    script = Path(__file__).resolve()
    home = Path(os.path.expanduser("~")).resolve()
    try:
        return 'python3 "$HOME/{}"'.format(script.relative_to(home).as_posix())
    except ValueError:
        return "python3 {}".format(shlex.quote(str(script)))


def settings_file():
    return Path(os.path.expanduser("~")) / ".claude" / "settings.json"


def load_settings(path):
    if not path.exists() or not path.read_text(encoding="utf-8").strip():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_settings(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.with_suffix(path.suffix + ".bak").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def registers_this_hook(group):
    return any(
        SCRIPT_NAME in (hook or {}).get("command", "")
        for hook in group.get("hooks", [])
        if isinstance(hook, dict)
    )


def install():
    path = settings_file()
    try:
        settings = load_settings(path)
    except json.JSONDecodeError as error:
        print("Could not parse {}: {}".format(path, error), file=sys.stderr)
        print("Fix the file, or add this entry by hand:", file=sys.stderr)
        print(json.dumps(hook_entry(), indent=2), file=sys.stderr)
        return 1

    groups = settings.setdefault("hooks", {}).setdefault(HOOK_EVENT, [])
    if any(registers_this_hook(group) for group in groups if isinstance(group, dict)):
        print("Already installed in {}".format(path))
        return 0

    groups.append(hook_entry())
    save_settings(path, settings)
    print("Installed the destructive-command hook in {}".format(path))
    print("Restart Claude Code (or run /hooks) to pick it up.")
    return 0


def hook_entry():
    return {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": hook_command_string()}],
    }


def uninstall():
    path = settings_file()
    try:
        settings = load_settings(path)
    except json.JSONDecodeError as error:
        print("Could not parse {}: {}".format(path, error), file=sys.stderr)
        return 1

    hooks = settings.get("hooks")
    if not isinstance(hooks, dict) or HOOK_EVENT not in hooks:
        print("Not installed in {}".format(path))
        return 0

    remaining = []
    removed = False
    for group in hooks[HOOK_EVENT]:
        if isinstance(group, dict) and registers_this_hook(group):
            group["hooks"] = [
                hook
                for hook in group.get("hooks", [])
                if not (isinstance(hook, dict) and SCRIPT_NAME in hook.get("command", ""))
            ]
            removed = True
            if not group["hooks"]:
                continue
        remaining.append(group)

    if not removed:
        print("Not installed in {}".format(path))
        return 0

    if remaining:
        hooks[HOOK_EVENT] = remaining
    else:
        del hooks[HOOK_EVENT]
    if not hooks:
        del settings["hooks"]
    save_settings(path, settings)
    print("Removed the destructive-command hook from {}".format(path))
    return 0


def check(command):
    rule = analyze(command)
    if rule is None:
        print("ALLOW: {}".format(command))
        return 0
    print("BLOCK: {}".format(command))
    print(denial_message(rule, command, logged=False))
    return 1


def main(argv):
    if not argv:
        return run_hook()
    if argv[0] == "--install":
        return install()
    if argv[0] == "--uninstall":
        return uninstall()
    if argv[0] == "--check" and len(argv) > 1:
        return check(" ".join(argv[1:]))
    print(__doc__.strip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as error:  # never break a session because of this hook
        json.dump(
            {
                "systemMessage": "destructive-command hook failed: {}".format(error),
            },
            sys.stdout,
        )
        sys.exit(0)
