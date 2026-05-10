#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code hook JSON from stdin. When a Bash command matches a
blocked pattern, it logs the attempt and returns a PreToolUse denial using the
current hookSpecificOutput.permissionDecision format.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOOK_COMMAND = "python3 ~/.claude/hooks/destructive_bash_guard.py"
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"


class BlockResult:
    def __init__(self, blocked: bool, reason: str = "") -> None:
        self.blocked = blocked
        self.reason = reason


def split_shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        flags = ""
        for candidate in tokens[index + 1 :]:
            if candidate == "--":
                break
            if not candidate.startswith("-") or candidate == "-":
                continue
            flags += candidate.lstrip("-").lower()

        if "r" in flags and "f" in flags:
            return True

    return False


def has_git_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        try:
            push_index = tokens.index("push", index + 1)
        except ValueError:
            continue
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in tokens[push_index + 1 :]):
            return True
    return False


def delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        match = re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE)
        if not match:
            continue
        tail = statement[match.end() :]
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            return True
    return False


def classify_command(command: str) -> BlockResult:
    tokens = split_shell_words(command)

    if has_rm_rf(tokens):
        return BlockResult(True, "rm with recursive and force flags can delete large directory trees")

    if has_git_force_push(tokens):
        return BlockResult(True, "git force-push can rewrite shared remote history")

    if re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
        return BlockResult(True, "DROP TABLE can destroy database schema and data")

    if re.search(r"\bTRUNCATE\b", command, re.IGNORECASE):
        return BlockResult(True, "TRUNCATE removes all rows from a table")

    if delete_without_where(command):
        return BlockResult(True, "DELETE FROM without a WHERE clause can wipe an entire table")

    return BlockResult(False)


def project_path(payload: dict[str, Any]) -> str:
    return (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def append_log(command: str, reason: str, project: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project,
        "reason": reason,
        "command": command,
    }
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def denial_payload(reason: str, command: str, project: str) -> dict[str, Any]:
    return {
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive Bash command before execution.\n"
                f"Reason: {reason}\n"
                f"Project: {project}\n"
                f"Command: {command}\n"
                f"Log: {LOG_FILE}"
            ),
        },
    }


def run_hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") not in {None, "PreToolUse"}:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    result = classify_command(command)
    if not result.blocked:
        return 0

    project = project_path(payload)
    append_log(command, result.reason, project)
    print(json.dumps(denial_payload(result.reason, command, project), ensure_ascii=True))
    return 0


def install_settings() -> int:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = SETTINGS_FILE.with_suffix(".json.bak")
            SETTINGS_FILE.replace(backup)
            settings = {}
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    for existing in pre_tool:
        if not isinstance(existing, dict):
            continue
        if existing.get("matcher") != "Bash":
            continue
        existing_hooks = existing.setdefault("hooks", [])
        if any(hook.get("command") == HOOK_COMMAND for hook in existing_hooks if isinstance(hook, dict)):
            break
        existing_hooks.append(entry["hooks"][0])
        break
    else:
        pre_tool.append(entry)

    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Registered destructive Bash guard in {SETTINGS_FILE}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-settings", action="store_true")
    args = parser.parse_args()

    if args.install_settings:
        return install_settings()

    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
