#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


LOG_PATH = Path(os.environ.get("CLAUDE_HOOK_BLOCK_LOG", "~/.claude/hooks/blocked.log")).expanduser()


class BlockReason:
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message


def normalize_command(command: str) -> str:
    """Normalize shell continuations and whitespace without changing meaning."""
    command = command.replace("\\\n", " ")
    command = command.replace("\r", "\n")
    return re.sub(r"[ \t]+", " ", command).strip()


def has_rm_rf(command: str) -> bool:
    """Detect rm invocations that combine recursive and force flags."""
    pattern = re.compile(
        r"(?is)(^|[;&|]\s*)rm\s+"
        r"(?:(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*)|"
        r"(?:-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)|"
        r"(?:-[A-Za-z]*r[A-Za-z]*(?:\s+\S+)*\s+-[A-Za-z]*f[A-Za-z]*)|"
        r"(?:-[A-Za-z]*f[A-Za-z]*(?:\s+\S+)*\s+-[A-Za-z]*r[A-Za-z]*))"
    )
    return bool(pattern.search(command))


def has_git_force_push(command: str) -> bool:
    """Detect force-pushing with git push."""
    pattern = re.compile(
        r"(?is)(^|[;&|]\s*)git\s+push\b(?=[^;&|]*(?:--force\b|--force-with-lease\b|(?:^|\s)-f(?:\s|$)))"
    )
    return bool(pattern.search(command))


def has_drop_table(command: str) -> bool:
    return bool(re.search(r"(?is)\bdrop\s+table\b", command))


def has_truncate(command: str) -> bool:
    return bool(re.search(r"(?is)\btruncate(?:\s+table)?\b", command))


def delete_segments(command: str) -> Iterable[str]:
    for match in re.finditer(r"(?is)\bdelete\s+from\b", command):
        tail = command[match.start() :]
        segment = tail.split(";", 1)[0]
        yield segment


def has_delete_without_where(command: str) -> bool:
    for segment in delete_segments(command):
        if not re.search(r"(?is)\bwhere\b", segment):
            return True
    return False


def find_block_reason(command: str) -> Optional[BlockReason]:
    normalized = normalize_command(command)

    checks = (
        (has_rm_rf, "rm-rf", "Blocked `rm -rf`: recursive forced deletion can remove large parts of the filesystem."),
        (has_git_force_push, "git-force-push", "Blocked `git push --force`: force pushes can rewrite shared history."),
        (has_drop_table, "drop-table", "Blocked `DROP TABLE`: dropping tables can destroy schema and data."),
        (has_truncate, "truncate", "Blocked `TRUNCATE`: truncation can erase table contents."),
        (
            has_delete_without_where,
            "delete-without-where",
            "Blocked `DELETE FROM` without `WHERE`: unqualified deletes can erase every row.",
        ),
    )

    for predicate, code, message in checks:
        if predicate(normalized):
            return BlockReason(code, message)

    return None


def extract_command(payload: Dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    return command if isinstance(command, str) else ""


def log_blocked_attempt(command: str, project_path: str, reason: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "project_path": project_path,
        "command": command,
        "reason": reason.code,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny_response(
    command: str,
    project_path: str,
    reason: BlockReason,
    log_error: Optional[str] = None,
) -> Dict[str, Any]:
    message = (
        f"{reason.message}\n\n"
        "The Bash tool call was not executed. Choose a safer command, narrow the target, "
        "or ask the user for explicit confirmation before attempting a destructive operation.\n\n"
        f"Project path: `{project_path or 'unknown'}`\n"
        f"Attempted command: `{command}`"
    )
    if log_error:
        message += f"\n\nNote: the hook also tried to write `blocked.log`, but logging failed: {log_error}"

    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
        },
        "systemMessage": message,
    }


def handle(payload: Dict[str, Any]) -> Dict[str, Any]:
    if payload.get("hook_event_name") != "PreToolUse":
        return {}

    if payload.get("tool_name") != "Bash":
        return {}

    command = extract_command(payload)
    if not command:
        return {}

    reason = find_block_reason(command)
    if reason is None:
        return {}

    project_path = payload.get("cwd") or payload.get("project_path") or ""
    log_error = None
    try:
        log_blocked_attempt(command, str(project_path), reason)
    except Exception as exc:
        log_error = str(exc)
    return deny_response(command, str(project_path), reason, log_error)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({}))
        return 0

    try:
        response = handle(payload)
    except Exception as exc:
        response = {"systemMessage": f"destructive-command hook error: {exc}"}

    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
