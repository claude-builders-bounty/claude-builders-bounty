#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
from pathlib import Path
import re
import shlex
import sys
from typing import Any


SQL_DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
SQL_TRUNCATE = re.compile(r"\btruncate\b", re.IGNORECASE)
SQL_DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
SQL_WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(command: str) -> bool:
    tokens = shell_tokens(command)

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        recursive = False
        force = False
        for option in tokens[index + 1 :]:
            if not option.startswith("-"):
                break
            if "r" in option.lower() or "R" in option:
                recursive = True
            if "f" in option.lower():
                force = True
            if recursive and force:
                return True

    return bool(re.search(r"\brm\s+-[^\s;|&]*r[^\s;|&]*f|\brm\s+-[^\s;|&]*f[^\s;|&]*r", command, re.IGNORECASE))


def has_force_push(command: str) -> bool:
    tokens = shell_tokens(command)

    for index in range(len(tokens) - 2):
        if tokens[index : index + 2] != ["git", "push"]:
            continue

        for option in tokens[index + 2 :]:
            if option == "--":
                break
            if option in {"--force", "--force-with-lease", "-f"} or option.startswith("--force="):
                return True

    return bool(re.search(r"\bgit\s+push\b[^\n;&|]*\s(--force(?:-with-lease)?|-f)\b", command))


def has_delete_without_where(command: str) -> bool:
    for statement in command.split(";"):
        if SQL_DELETE_FROM.search(statement) and not SQL_WHERE.search(statement):
            return True
    return False


def blocked_reason(command: str) -> str | None:
    if has_rm_rf(command):
        return "rm -rf"
    if SQL_DROP_TABLE.search(command):
        return "DROP TABLE"
    if has_force_push(command):
        return "git push --force"
    if SQL_TRUNCATE.search(command):
        return "TRUNCATE"
    if has_delete_without_where(command):
        return "DELETE FROM without WHERE"
    return None


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_name": "Bash", "tool_input": {"command": raw}}
    return payload if isinstance(payload, dict) else {}


def bash_command(payload: dict[str, Any]) -> str:
    tool_name = payload.get("tool_name")
    if tool_name and tool_name != "Bash":
        return ""

    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
        return command if isinstance(command, str) else ""

    return ""


def project_path(payload: dict[str, Any]) -> str:
    for key in ("CLAUDE_PROJECT_DIR", "PWD"):
        value = os.environ.get(key)
        if value:
            return value

    for key in ("cwd", "project_dir", "workspace_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def log_block(payload: dict[str, Any], command: str, reason: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = f"{timestamp}\t{project_path(payload)}\t{reason}\t{command}\n"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(line)


def deny_output(command: str, reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command ({reason}). "
                f"Review the command before running it manually: {command}"
            ),
        }
    }


def install_hook() -> int:
    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        with settings_path.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    script_path = Path(__file__).expanduser().resolve()
    command = f'"{sys.executable}" "{script_path}"'
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command}],
    }

    if entry not in pre_tool:
        pre_tool.append(entry)

    with settings_path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed destructive command hook in {settings_path}")
    return 0


def run_hook() -> int:
    payload = load_payload()
    command = bash_command(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    log_block(payload, command, reason)
    print(json.dumps(deny_output(command, reason)))
    return 0


def main() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        return install_hook()
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
