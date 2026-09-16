#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads a Claude Code hook event JSON on stdin (tool_name + tool_input),
exits non-zero with a clear reason when the command is destructive, and
logs every blocked attempt to ~/.claude/hooks/blocked.log.

Safe commands pass through untouched (exit 0).
"""
import json
import os
import re
import shlex
import sys
import datetime

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# SQL destructive forms must begin a statement (after a command separator or
# at line start) so that `echo DROP TABLE` or a commit message mentioning the
# words is not falsely blocked.
SQL_LEAD = r"(?:^|;|&&|\|\||\||&\s)"

BLOCK_PATTERNS = [
    (re.compile(SQL_LEAD + r"\s*DROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(SQL_LEAD + r"\s*TRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(SQL_LEAD + r"\s*DELETE\s+FROM\b(?![^\n]*\bWHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE"),
    (re.compile(r"\bgit\s+push\b[^\n]*(?:--force\b|--force-with-lease\b|\s-f\b)", re.IGNORECASE), "git push --force"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard"),
    (re.compile(r"\bgit\s+clean\b(?![^\n]*(?:-n\b|--dry-run))", re.IGNORECASE), "git clean"),
]


def rm_is_recursive_force(command: str):
    """True if the line runs rm with both recursive and force flags.

    Token-scans so flags belonging to a later command on the same line
    (e.g. `rm dir && grep -f pat f`) are not conflated with rm's own.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if os.path.basename(tok) == "rm":
            has_r = has_f = False
            j = i + 1
            while j < len(tokens):
                arg = tokens[j]
                if arg == "--":
                    break
                if arg.startswith("--"):
                    if arg in ("--recursive", "-R") or arg.startswith("--recursive"):
                        has_r = True
                    if arg.startswith("--force"):
                        has_f = True
                    j += 1
                    continue
                if arg.startswith("-") and len(arg) > 1:
                    flags = arg[1:]
                    if "r" in flags or "R" in flags:
                        has_r = True
                    if "f" in flags:
                        has_f = True
                    j += 1
                    continue
                break
            if has_r and has_f:
                return "rm -rf recursive force deletion"
        i += 1
    return None


def find_reason(command: str):
    reason = rm_is_recursive_force(command)
    if reason:
        return reason
    for pattern, reason in BLOCK_PATTERNS:
        if pattern.search(command):
            return reason
    return None


def log_blocked(command: str, project_path: str, reason: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {
                        "timestamp": ts,
                        "project_path": project_path,
                        "command": command,
                        "reason": reason,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    except OSError:
        return


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = event.get("tool_name")
    if tool_name and tool_name != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not command or not isinstance(command, str):
        return 0

    reason = find_reason(command)
    if not reason:
        return 0

    project_path = event.get("project_path") or os.getcwd()
    log_blocked(command, project_path, reason)

    sys.stderr.write(
        f"BLOCKED: destructive command detected ({reason}).\n"
        f"Command: {command}\n"
        f"Audit trail: {LOG_PATH}\n"
        "Choose a safer alternative (dry-run, targeted removal, WHERE clause, non-force push).\n"
    )
    # Exit code 2 tells Claude Code to stop the call and show stderr to Claude.
    return 2


if __name__ == "__main__":
    sys.exit(main())