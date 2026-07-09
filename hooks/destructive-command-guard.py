#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads Claude Code hook JSON from stdin. For unsafe Bash commands, logs the
attempt and exits 2 with a clear reason on stderr, which blocks the tool call.
For safe or non-Bash tool calls, exits 0 silently.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


class BlockReason:
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Invalid hook input should not block normal work.
        return {}
    return payload if isinstance(payload, dict) else {}


def hook_log_path() -> Path:
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE")
    if home:
        return Path(home) / ".claude" / "hooks" / "blocked.log"
    try:
        return Path.home() / ".claude" / "hooks" / "blocked.log"
    except RuntimeError:
        return Path.cwd() / ".claude" / "hooks" / "blocked.log"


def command_from_payload(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("toolName") or payload.get("tool")
    if not isinstance(tool_name, str):
        # Claude Code PreToolUse payloads for Bash include tool_input.command.
        return bool(command_from_payload(payload))
    return tool_name.lower() == "bash"


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath", "workspace"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    env = payload.get("environment")
    if isinstance(env, dict):
        pwd = env.get("PWD")
        if isinstance(pwd, str) and pwd:
            return pwd
    return os.getcwd()


def strip_quoted_text(command: str) -> str:
    # Avoid blocking innocent examples like: echo "rm -rf /".
    return re.sub(r"""(['"])(?:\\.|(?!\1).)*\1""", " ", command)


def shell_statements(command: str) -> list[str]:
    parts = re.split(r";|&&|\|\|", command)
    return [part.strip() for part in parts if part.strip()]


def delete_without_where(command: str) -> bool:
    for statement in shell_statements(command):
        for match in re.finditer(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
            tail = statement[match.end() :]
            if not re.search(r"\bwhere\b", tail, flags=re.IGNORECASE):
                return True
    return False


def has_forced_recursive_rm(command: str) -> bool:
    for match in re.finditer(r"(^|[;&|]\s*)(?:sudo\s+)?(?:command\s+)?rm\s+((?:-[a-zA-Z]+\s*)+)", command):
        flags = re.sub(r"[^a-zA-Z]", "", match.group(2)).lower()
        if "r" in flags and "f" in flags:
            return True
    return False


def blocked_reason(command: str) -> BlockReason | None:
    shell_text = strip_quoted_text(command)

    if has_forced_recursive_rm(shell_text):
        return BlockReason("rm-rf", "rm -rf style recursive forced deletion is blocked")

    if re.search(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\s|=|$|-with-lease\b)", shell_text, flags=re.IGNORECASE):
        return BlockReason("git-push-force", "force pushing is blocked")

    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return BlockReason("drop-table", "DROP TABLE is blocked")

    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return BlockReason("truncate", "TRUNCATE is blocked")

    if delete_without_where(command):
        return BlockReason("delete-without-where", "DELETE FROM without a WHERE clause is blocked")

    return None


def append_block_log(command: str, payload: dict[str, Any], reason: BlockReason) -> None:
    log_path = hook_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason.code,
        "attempted_command": command,
        "project_path": project_path(payload),
    }
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
    payload = load_payload()
    if not is_bash_tool(payload):
        return 0

    command = command_from_payload(payload)
    if not command.strip():
        return 0

    reason = blocked_reason(command)
    if not reason:
        return 0

    append_block_log(command, payload, reason)
    print(
        f"Blocked destructive Bash command: {reason.message}. "
        f"Edit the command to use a safer, targeted operation.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
