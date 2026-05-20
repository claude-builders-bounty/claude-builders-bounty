#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


SQL_STATEMENT_SPLIT_RE = re.compile(r";+")


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _contains_rm_rf(command: str) -> bool:
    command = _compact(command)
    for match in re.finditer(r"(?:^|[;&|]\s*)rm\s+([^;&|]+)", command):
        args = match.group(1)
        short_flags = "".join(re.findall(r"(?<!\S)-([A-Za-z]+)\b", args))
        has_recursive = "r" in short_flags or bool(re.search(r"(?:^|\s)--recursive(?:\s|$)", args))
        has_force = "f" in short_flags or bool(re.search(r"(?:^|\s)--force(?:\s|$)", args))
        if has_recursive and has_force:
            return True
    return False


def _contains_forced_git_push(command: str) -> bool:
    return bool(
        re.search(
            r"(^|[;&|]\s*)git\s+push\b(?:(?![;&|]).)*(?:--force(?:-with-lease)?\b|-f\b)",
            _compact(command),
            re.IGNORECASE,
        )
    )


def _contains_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, re.IGNORECASE))


def _contains_truncate(command: str) -> bool:
    return bool(re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE))


def _contains_delete_without_where(command: str) -> bool:
    for statement in SQL_STATEMENT_SPLIT_RE.split(command):
        statement = _compact(statement)
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return True
    return False


RULES = (
    ("rm -rf", _contains_rm_rf),
    ("forced git push", _contains_forced_git_push),
    ("DROP TABLE", _contains_drop_table),
    ("TRUNCATE", _contains_truncate),
    ("DELETE FROM without WHERE", _contains_delete_without_where),
)


def find_block_reason(command: str) -> str | None:
    for label, predicate in RULES:
        if predicate(command):
            return label
    return None


def _project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "workspace_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def _claude_hooks_dir() -> Path:
    config_home = os.environ.get("CLAUDE_CONFIG_HOME")
    if config_home:
        return Path(config_home) / "hooks"

    home = Path(os.environ.get("HOME") or Path.home())
    return home / ".claude" / "hooks"


def _log_block(command: str, project_path: str, reason: str) -> None:
    hook_dir = _claude_hooks_dir()
    hook_dir.mkdir(parents=True, exist_ok=True)
    log_path = hook_dir / "blocked.log"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _decision(decision: str, reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any] | None:
    tool_name = payload.get("tool_name")
    tool_input = payload.get("tool_input") if isinstance(payload.get("tool_input"), dict) else {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None

    if tool_name != "Bash" or not isinstance(command, str):
        return None

    reason = find_block_reason(command)
    if reason is None:
        return None

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    return _decision(
        "deny",
        (
            "Blocked potentially destructive Bash command. "
            f"Matched policy: {reason}. "
            "Ask the user for explicit confirmation or use a safer, scoped command."
        ),
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(
            json.dumps(
                _decision("deny", f"Blocked because hook input was not valid JSON: {exc}")
            )
        )
        return 0

    decision = evaluate(payload)
    if decision is not None:
        print(json.dumps(decision))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
