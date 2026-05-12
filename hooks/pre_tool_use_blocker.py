#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

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


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install this script as a Bash PreToolUse hook in ~/.claude/settings.json.",
    )
    args = parser.parse_args()

    if args.install:
        install_hook(Path(__file__).resolve())
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    decision = evaluate_payload(payload)
    if not decision:
        return 0

    command = get_command(payload)
    project_path = get_project_path(payload)
    log_blocked_attempt(command, project_path, decision)
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": decision,
                }
            }
        )
    )
    return 0


def evaluate_payload(payload: dict[str, Any]) -> str | None:
    if payload.get("hook_event_name") != "PreToolUse":
        return None
    if payload.get("tool_name") != "Bash":
        return None

    command = get_command(payload)
    if not command:
        return None

    checks = [
        (is_rm_rf, "Blocked destructive recursive delete command: rm -rf."),
        (is_drop_table, "Blocked SQL schema destruction command: DROP TABLE."),
        (is_git_push_force, "Blocked history-rewriting push command: git push --force."),
        (is_truncate, "Blocked destructive SQL command: TRUNCATE."),
        (is_delete_without_where, "Blocked DELETE FROM command without a WHERE clause."),
    ]

    for predicate, reason in checks:
        if predicate(command):
            return reason
    return None


def get_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def get_project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_rm_rf(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        options = tokens[index + 1 :]
        has_recursive = False
        has_force = False
        for option in options:
            if not option.startswith("-"):
                break
            if option in {"--recursive", "--dir"}:
                has_recursive = True
            if option == "--force":
                has_force = True
            if option.startswith("-") and not option.startswith("--"):
                has_recursive = has_recursive or "r" in option or "R" in option
                has_force = has_force or "f" in option
        if has_recursive and has_force:
            return True
    return False


def is_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, re.IGNORECASE))


def is_git_push_force(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    for index, token in enumerate(tokens):
        if token != "git":
            continue
        if index + 1 >= len(tokens) or tokens[index + 1] != "push":
            continue
        push_args = tokens[index + 2 :]
        return any(arg in {"--force", "-f", "--force-with-lease"} for arg in push_args)
    return False


def is_truncate(command: str) -> bool:
    return bool(re.search(r"\btruncate\b", command, re.IGNORECASE))


def is_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def install_hook(script_path: Path) -> None:
    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        with settings_path.open("r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
    else:
        settings = {}

    hook_command = f"python3 {shlex.quote(str(script_path))}"
    hook_entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": hook_command,
            }
        ],
    }

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    already_installed = any(
        entry.get("matcher") == "Bash"
        and any(hook.get("command") == hook_command for hook in entry.get("hooks", []))
        for entry in pre_tool_use
        if isinstance(entry, dict)
    )
    if not already_installed:
        pre_tool_use.append(hook_entry)

    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed PreToolUse Bash blocker in {settings_path}")


if __name__ == "__main__":
    raise SystemExit(main())
