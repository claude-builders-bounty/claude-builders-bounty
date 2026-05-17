#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOKS_DIR = Path.home() / ".claude" / "hooks"
HOOK_PATH = HOOKS_DIR / "block_destructive_commands.py"
LOG_PATH = HOOKS_DIR / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"\brm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b"),
        "Recursive force removal is blocked.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "Dropping database tables is blocked.",
    ),
    (
        "git push --force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b", re.IGNORECASE),
        "Force-pushing Git history is blocked.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "Truncating database data is blocked.",
    ),
)

DELETE_FROM_STATEMENT_RE = re.compile(r"\bDELETE\s+FROM\b[^;]*", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""

    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    return payload.get("tool_name") == "Bash"


def first_block_reason(command: str) -> str | None:
    for label, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return f"{reason} Matched pattern: {label}."

    for statement in DELETE_FROM_STATEMENT_RE.finditer(command):
        if not WHERE_RE.search(statement.group(0)):
            return "DELETE FROM without a WHERE clause is blocked. Matched pattern: DELETE FROM."

    return None


def project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd

    return os.getcwd()


def log_blocked_attempt(command: str, project: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = {
            "timestamp": timestamp,
            "command": command,
            "project_path": project,
        }
        with LOG_PATH.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError as error:
        print(f"warning: could not write blocked command log: {error}", file=sys.stderr)


def deny(reason: str) -> int:
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": f"Destructive command blocked by hook: {reason}",
            }
        )
    )
    return 0


def allow() -> int:
    print(json.dumps({"decision": "approve"}))
    return 0


def run(payload: dict[str, Any]) -> int:
    if not is_bash_tool(payload):
        return allow()

    command = extract_command(payload)
    reason = first_block_reason(command)
    if reason is None:
        return allow()

    log_blocked_attempt(command, project_path(payload))
    return deny(reason)


def hook_config() -> dict[str, Any]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python {HOOK_PATH}",
                        }
                    ],
                }
            ]
        }
    }


def merge_settings(existing: dict[str, Any]) -> dict[str, Any]:
    config = hook_config()
    existing_hooks = existing.setdefault("hooks", {})
    pre_tool_use = existing_hooks.setdefault("PreToolUse", [])
    candidate = config["hooks"]["PreToolUse"][0]

    if candidate not in pre_tool_use:
        pre_tool_use.append(candidate)

    return existing


def install() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__), HOOK_PATH)

    if SETTINGS_PATH.exists():
        with SETTINGS_PATH.open(encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    else:
        settings = {}

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(merge_settings(settings), settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed hook to {HOOK_PATH}")
    print(f"Updated settings at {SETTINGS_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install the hook into ~/.claude/hooks")
    args = parser.parse_args()

    if args.install:
        return install()

    try:
        payload = json.loads(sys.stdin.read().lstrip("\ufeff"))
    except json.JSONDecodeError:
        return allow()

    if not isinstance(payload, dict):
        return allow()

    return run(payload)


if __name__ == "__main__":
    raise SystemExit(main())
