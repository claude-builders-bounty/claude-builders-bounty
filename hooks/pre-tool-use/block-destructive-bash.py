#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "block-destructive-bash"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
INSTALL_COMMAND = str(Path.home() / ".claude" / "hooks" / "block-destructive-bash.py")


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--install"]:
        install_settings()
        print(f"Installed {HOOK_NAME} in {SETTINGS_PATH}")
        return 0
    if argv in (["--help"], ["-h"]):
        print("Usage: block-destructive-bash.py [--install]")
        return 0

    payload = read_payload(sys.stdin.read())
    command = extract_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    project_path = project_path_from(payload)
    log_blocked_attempt(command, project_path, reason)
    print(json.dumps(deny_response(reason), separators=(",", ":")))
    return 0


def read_payload(raw: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_command(payload: dict[str, Any]) -> str:
    tool_name = str(payload.get("tool_name", ""))
    if tool_name and tool_name != "Bash":
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def blocked_reason(command: str) -> str | None:
    if has_rm_rf(command):
        return "Blocked rm -rf because recursive forced deletion can cause irreversible data loss."
    if has_git_force_push(command):
        return "Blocked git push --force because it can rewrite shared branch history."
    if DROP_TABLE_RE.search(command):
        return "Blocked DROP TABLE because it can permanently remove schema and data."
    if TRUNCATE_RE.search(command):
        return "Blocked TRUNCATE because it can remove all rows without per-row safeguards."
    if has_delete_without_where(command):
        return "Blocked DELETE FROM without a WHERE clause because it can delete every row."
    return None


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(command: str) -> bool:
    words = shell_words(command)
    for index, word in enumerate(words):
        if basename(word) != "rm":
            continue
        flags = []
        for following in words[index + 1 :]:
            if not following.startswith("-") or following == "-":
                break
            flags.append(following)
        joined_flags = "".join(flags)
        if "r" in joined_flags and "f" in joined_flags:
            return True
    return False


def has_git_force_push(command: str) -> bool:
    words = shell_words(command)
    for index, word in enumerate(words):
        if basename(word) != "git":
            continue
        rest = words[index + 1 :]
        if "push" not in rest:
            continue
        push_index = rest.index("push")
        flags = set(rest[push_index + 1 :])
        if {"--force", "-f", "--force-with-lease"} & flags:
            return True
    return False


def has_delete_without_where(command: str) -> bool:
    for statement in command.split(";"):
        if DELETE_FROM_RE.search(statement) and not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def basename(word: str) -> str:
    return word.rsplit("/", 1)[-1]


def project_path_from(payload: dict[str, Any]) -> str:
    candidates = [
        payload.get("cwd"),
        payload.get("project_path"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.environ.get("PWD"),
    ]
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return os.getcwd()


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def deny_response(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def install_settings() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    settings = load_settings()
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    hook_group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": INSTALL_COMMAND,
            }
        ],
    }
    if hook_group not in pre_tool_use:
        pre_tool_use.append(hook_group)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_settings() -> dict[str, Any]:
    if not SETTINGS_PATH.exists():
        return {}
    try:
        loaded = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup = SETTINGS_PATH.with_suffix(".json.bak")
        SETTINGS_PATH.replace(backup)
        return {}
    return loaded if isinstance(loaded, dict) else {}


if __name__ == "__main__":
    raise SystemExit(main())
