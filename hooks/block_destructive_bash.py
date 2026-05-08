#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"
BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", " ", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


def has_rm_recursive_force(command: str) -> bool:
    try:
        parts = shlex.split(command, posix=os.name != "nt")
    except ValueError:
        parts = command.split()

    for index, part in enumerate(parts):
        if part != "rm":
            continue

        flags = set()
        for next_part in parts[index + 1 :]:
            if next_part == "--":
                break
            if not next_part.startswith("-"):
                break
            if next_part in {"--recursive", "--dir"}:
                flags.add("r")
            if next_part == "--force":
                flags.add("f")
            if next_part.startswith("--"):
                continue
            for char in next_part[1:]:
                flags.add(char)

        if {"r", "f"}.issubset(flags):
            return True

    return False


def delete_without_where(command: str) -> bool:
    sql = strip_sql_comments(command)
    for match in re.finditer(r"\bdelete\s+from\b", sql, flags=re.IGNORECASE):
        statement_tail = sql[match.end() :]
        statement = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    normalized = normalize_command(command)

    if has_rm_recursive_force(normalized):
        return "Blocked destructive recursive delete command: rm with recursive and force flags."

    checks = [
        (r"\bdrop\s+table\b", "Blocked destructive SQL command: DROP TABLE."),
        (r"\btruncate\b", "Blocked destructive SQL command: TRUNCATE."),
        (r"\bgit\s+push\b(?=.*(?:--force|-f)\b)", "Blocked destructive Git command: git push --force."),
    ]

    for pattern, message in checks:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            return message

    if delete_without_where(normalized):
        return "Blocked destructive SQL command: DELETE FROM without a WHERE clause."

    return None


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    record = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny(reason: str, command: str, project_path: str) -> None:
    log_blocked_attempt(command, project_path, reason)
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{reason} The attempted Bash command was logged to {BLOCKED_LOG}."
            ),
        }
    }
    print(json.dumps(response))
    raise SystemExit(0)


def handle_hook() -> int:
    try:
        payload: dict[str, Any] = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude hook JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    project_path = str(
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or Path.cwd()
    )

    reason = find_block_reason(command)
    if reason:
        deny(reason, command, project_path)

    return 0


def install_hook() -> int:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / HOOK_NAME
    source = Path(__file__).resolve()

    if source != target:
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    settings: dict[str, Any] = {}
    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))

    settings.setdefault("hooks", {})
    settings["hooks"].setdefault("PreToolUse", [])

    command = f"python {target}"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    existing = settings["hooks"]["PreToolUse"]
    if not any(item.get("matcher") == "Bash" and item.get("hooks") == entry["hooks"] for item in existing):
        existing.append(entry)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {HOOK_NAME} and registered PreToolUse Bash hook in {SETTINGS_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash tool calls.")
    parser.add_argument("--install", action="store_true", help="Install hook into ~/.claude/hooks and settings.json")
    parser.add_argument("--check-command", help="Test one command and print the matched block reason")
    args = parser.parse_args()

    if args.install:
        return install_hook()

    if args.check_command is not None:
        reason = find_block_reason(args.check_command)
        if reason:
            print(reason)
            return 2
        print("allowed")
        return 0

    return handle_hook()


if __name__ == "__main__":
    raise SystemExit(main())

