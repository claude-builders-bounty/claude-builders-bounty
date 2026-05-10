#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


def normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip()


def detect_rm_rf(command: str) -> str | None:
    rm_command = re.compile(
        r"(?:^|[;&|]\s*)(?:sudo\s+)?rm\s+([^;&|]*)",
        re.IGNORECASE,
    )
    for match in rm_command.finditer(command):
        args = match.group(1)
        compact_flags = "".join(re.findall(r"(?<!\w)-[A-Za-z]+", args))
        has_recursive = bool(
            re.search(r"(^|\s)--recursive(\s|$)", args)
            or "r" in compact_flags
            or "R" in compact_flags
        )
        has_force = bool(
            re.search(r"(^|\s)--force(\s|$)", args) or "f" in compact_flags
        )
        if has_recursive and has_force:
            return "rm with recursive and force flags"
    return None


def detect_git_force_push(command: str) -> str | None:
    git_push = re.compile(
        r"(?:^|[;&|]\s*)(?:sudo\s+)?(?:env\s+[^;&|]*\s+)?git\s+push\b([^;&|]*)",
        re.IGNORECASE,
    )
    for match in git_push.finditer(command):
        args = match.group(1)
        if re.search(r"(^|\s)(--force|--force-with-lease|-f)(=|\s|$)", args):
            return "git push with force flag"
    return None


def detect_sql_destructive(command: str) -> str | None:
    flattened = normalize(command)
    upper = flattened.upper()

    if re.search(r"\bDROP\s+TABLE\b", upper):
        return "DROP TABLE statement"

    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", upper):
        return "TRUNCATE statement"

    delete_match = re.search(r"\bDELETE\s+FROM\b", upper)
    if delete_match:
        tail = upper[delete_match.start() :]
        statement = re.split(r";|&&|\|\||\n", tail, maxsplit=1)[0]
        if not re.search(r"\bWHERE\b", statement):
            return "DELETE FROM without WHERE clause"

    return None


def detect_block_reason(command: str) -> str | None:
    checks = (
        detect_rm_rf,
        detect_git_force_push,
        detect_sql_destructive,
    )
    for check in checks:
        reason = check(command)
        if reason:
            return reason
    return None


def log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str) -> None:
    message = (
        "Blocked destructive Bash command: "
        f"{reason}. Use a safer command or ask the user for an explicit recovery plan."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )


def run_hook(payload: dict[str, Any]) -> int:
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = detect_block_reason(command)
    if not reason:
        return 0

    project_path = str(
        payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    )
    log_block(command, project_path, reason)
    deny(reason)
    return 0


def install_settings() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open(encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = "python3 ~/.claude/hooks/block-dangerous-bash.py"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }

    already_installed = any(
        item.get("matcher") == "Bash"
        and any(hook.get("command") == command for hook in item.get("hooks", []))
        for item in pre_tool_use
        if isinstance(item, dict)
    )
    if not already_installed:
        pre_tool_use.append(entry)

    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed PreToolUse hook in {SETTINGS_PATH}")
    return 0


def self_test() -> int:
    blocked = [
        "rm -rf /tmp/build",
        "sudo rm -fr node_modules",
        "git push --force origin main",
        "sqlite3 app.db 'DROP TABLE users;'",
        "psql -c 'TRUNCATE sessions;'",
        "sqlite3 app.db 'DELETE FROM users;'",
    ]
    allowed = [
        "npm test",
        "git push origin main",
        "rm -r build-cache",
        "sqlite3 app.db 'DELETE FROM users WHERE id = 1;'",
        "sqlite3 app.db 'SELECT * FROM users;'",
    ]

    failures: list[str] = []
    for command in blocked:
        if not detect_block_reason(command):
            failures.append(f"expected block: {command}")
    for command in allowed:
        if detect_block_reason(command):
            failures.append(f"expected allow: {command}")

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1

    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Block destructive Claude Code Bash tool calls."
    )
    parser.add_argument("--install-settings", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.install_settings:
        return install_settings()
    if args.self_test:
        return self_test()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    return run_hook(payload)


if __name__ == "__main__":
    raise SystemExit(main())
