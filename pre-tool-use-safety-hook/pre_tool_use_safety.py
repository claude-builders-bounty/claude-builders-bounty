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
from typing import Any


BLOCK_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def shell_words(command: str) -> list[str]:
    """尽量按 Bash 语义拆分命令，失败时回退到空列表以便正则兜底。"""
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def option_has_recursive_force(option: str) -> bool:
    """识别 rm 的组合短参数，例如 -rf、-fr、-Rf。"""
    if not option.startswith("-") or option == "-":
        return False
    normalized = option.lstrip("-").lower()
    return "r" in normalized and "f" in normalized


def has_rm_rf(command: str, words: list[str]) -> bool:
    for index, word in enumerate(words):
        if word != "rm":
            continue
        for option in words[index + 1 :]:
            if option == "--":
                break
            if not option.startswith("-"):
                continue
            if option == "--force":
                continue
            if option in {"-r", "-R", "--recursive"}:
                remaining = words[index + 1 :]
                if any(item in {"-f", "--force"} for item in remaining):
                    return True
            if option in {"-f", "--force"}:
                remaining = words[index + 1 :]
                if any(item in {"-r", "-R", "--recursive"} for item in remaining):
                    return True
            if option_has_recursive_force(option):
                return True
    return bool(re.search(r"(?i)(?:^|[;&|]\s*)rm\s+(?:-[a-z]*r[a-z]*f|-?[a-z]*f[a-z]*r)", command))


def has_git_push_force(command: str, words: list[str]) -> bool:
    for index in range(len(words) - 2):
        if words[index : index + 2] != ["git", "push"]:
            continue
        if any(word in {"--force", "-f", "--force-with-lease"} for word in words[index + 2 :]):
            return True
    return bool(re.search(r"(?i)(?:^|[;&|]\s*)git\s+push\b[^;&|]*\s(?:--force|-f|--force-with-lease)\b", command))


def sql_statements(command: str) -> list[str]:
    """粗粒度切分 SQL 片段，避免多语句时 WHERE 泄漏到前一个 DELETE。"""
    return [statement.strip() for statement in re.split(r";|\n", command) if statement.strip()]


def has_delete_without_where(command: str) -> bool:
    for statement in sql_statements(command):
        if re.search(r"(?is)\bdelete\s+from\b", statement) and not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


def find_block_reason(command: str) -> str | None:
    words = shell_words(command)
    checks = [
        (has_rm_rf(command, words), "Blocked destructive filesystem command: rm -rf"),
        (has_git_push_force(command, words), "Blocked force push command: git push --force"),
        (bool(re.search(r"(?is)\bdrop\s+table\b", command)), "Blocked destructive SQL command: DROP TABLE"),
        (bool(re.search(r"(?is)\btruncate\b", command)), "Blocked destructive SQL command: TRUNCATE"),
        (has_delete_without_where(command), "Blocked unsafe SQL command: DELETE FROM without WHERE"),
    ]
    for matched, reason in checks:
        if matched:
            return reason
    return None


def project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    return os.getcwd()


def append_block_log(command: str, project: str, reason: str) -> None:
    BLOCK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    sanitized_command = command.replace("\r", "\\r").replace("\n", "\\n")
    sanitized_project = project.replace("\r", "\\r").replace("\n", "\\n")
    sanitized_reason = reason.replace("\r", "\\r").replace("\n", "\\n")
    with BLOCK_LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{sanitized_project}\t{sanitized_reason}\t{sanitized_command}\n")


def deny_response(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook input JSON: {exc}", file=sys.stderr)
        return 2

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    full_reason = f"{reason}. Command was blocked by the Claude Code safety hook."
    append_block_log(command=command, project=project_path(payload), reason=reason)
    print(json.dumps(deny_response(full_reason), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
