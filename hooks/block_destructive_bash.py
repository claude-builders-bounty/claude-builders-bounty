#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "SQL schema deletion (DROP TABLE)",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
    ),
    (
        "forced git push (git push --force)",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:\b|=)", re.IGNORECASE),
    ),
    (
        "SQL table truncation (TRUNCATE)",
        re.compile(r"\btruncate\b", re.IGNORECASE),
    ),
)

DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)
SQL_STATEMENT_SPLIT_RE = re.compile(r"[;\n]")


def contains_recursive_forced_rm(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return bool(re.search(r"(?<![\w-])rm\s+-[A-Za-z]*r[A-Za-z]*f\b", command))

    for index, token in enumerate(tokens):
        if Path(token).name != "rm":
            continue

        recursive = False
        force = False
        for option in tokens[index + 1 :]:
            if not option.startswith("-") or option == "-":
                break
            recursive = recursive or option in {"-r", "-R", "--recursive"} or (
                option.startswith("-") and not option.startswith("--") and "r" in option.lower()
            )
            force = force or option == "--force" or (
                option.startswith("-") and not option.startswith("--") and "f" in option
            )
        if recursive and force:
            return True

    return False


def find_block_reason(command: str) -> str | None:
    """Return the block reason for a dangerous command, or None when allowed."""
    if contains_recursive_forced_rm(command):
        return "recursive forced remove (rm -rf)"

    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return reason

    for statement in SQL_STATEMENT_SPLIT_RE.split(command):
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return "SQL mass deletion (DELETE FROM without WHERE)"

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / "blocked.log"
    timestamp = datetime.now(timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str, command: str) -> int:
    message = (
        "Blocked destructive Bash command: "
        f"{reason}. Review the command and ask the user for explicit approval "
        "before retrying with a safer, narrower operation."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))
    print(f"{message}\nCommand: {command}", file=sys.stderr)
    return 2


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Unable to parse Claude hook input JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if not reason:
        return 0

    project_path = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_blocked_attempt(command=command, project_path=str(project_path), reason=reason)
    return deny(reason, command)


if __name__ == "__main__":
    raise SystemExit(main())
