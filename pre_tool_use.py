#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code
Blocks dangerous bash commands before execution.

Bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3
"""

import json
import os
import sys
import shlex
import re
import datetime
import pathlib

LOG_DIR = pathlib.Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"

PATTERNS = []


def _check_rm_rf(tokens, raw_cmd):
    """Block rm only when BOTH recursive (-r) and force (-f) flags are present."""
    has_r, has_f = False, False
    for tok in tokens:
        if tok.startswith("-"):
            clean = tok.lstrip("-")
            has_r = has_r or ("r" in clean)
            has_f = has_f or ("f" in clean)
    return has_r and has_f


PATTERNS.append(("rm -rf", _check_rm_rf))


def _check_drop_table(tokens, raw_cmd):
    return bool(re.search(r"\bDROP\s+TABLE\b", raw_cmd, re.IGNORECASE))


PATTERNS.append(("DROP TABLE", _check_drop_table))


def _check_git_push_force(tokens, raw_cmd):
    return bool(
        re.search(r"\bgit\s+push\b.*?(?:--force|-f)\b", raw_cmd, re.IGNORECASE)
    )


PATTERNS.append(("git push --force", _check_git_push_force))


def _check_truncate(tokens, raw_cmd):
    return bool(re.search(r"\bTRUNCATE\b", raw_cmd, re.IGNORECASE))


PATTERNS.append(("TRUNCATE", _check_truncate))


def _check_delete_without_where(tokens, raw_cmd):
    """Block DELETE FROM only when no WHERE clause follows."""
    m = re.search(r"\bDELETE\s+FROM\b", raw_cmd, re.IGNORECASE)
    if not m:
        return False
    rest = raw_cmd[m.end():]
    if re.search(r"\bWHERE\b", rest, re.IGNORECASE):
        return False
    return True


PATTERNS.append(("DELETE FROM without WHERE", _check_delete_without_where))


def log_block(attempted_cmd, project_path, pattern_name):
    """Append a blocked-event entry to the log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = (
        f"[{ts}] BLOCKED: pattern={pattern_name}\n"
        f"  command: {attempted_cmd}\n"
        f"  project: {project_path}\n"
        f"{'-' * 60}\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def analyze_command(command_str):
    """Return (pattern_name, None) if dangerous, else (None, None)."""
    tokens = []
    try:
        tokens = shlex.split(command_str)
    except Exception:
        tokens = command_str.split()

    for name, checker in PATTERNS:
        try:
            if checker(tokens, command_str):
                return name
        except Exception:
            continue
    return None


def main():
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        json.dump({"error": "hook: unable to parse input"}, sys.stdout)
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if tool_name != "Bash":
        sys.exit(0)

    command = (tool_input.get("command") or "").strip()
    if not command:
        sys.exit(0)

    blocked_pattern = analyze_command(command)

    if blocked_pattern:
        project_path = os.getcwd()
        log_block(command, project_path, blocked_pattern)

        result = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"BLOCKED: {blocked_pattern}\n"
                    f"The command `{command}` matches a dangerous pattern "
                    f"and was prevented by the pre-tool-use safety hook.\n"
                    f"Logged to: {LOG_FILE}"
                ),
            }
        }
        json.dump(result, sys.stdout)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()