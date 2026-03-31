#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


BLOCK_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("rm -rf", re.compile(r"(?:^|[\s;&|])(?:sudo\s+)?rm\s+-[^\n]*(?:rf|fr|r\s+-f|-r\s+f|-r\s+-f)", re.IGNORECASE)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n]*\s(?:--force|-f)\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
)

DELETE_WITHOUT_WHERE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bwhere\b", re.IGNORECASE)


def default_log_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def parse_payload(raw_text: str) -> dict:
    if not raw_text.strip():
        return {}
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {}


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def extract_project_path(payload: dict) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd.strip():
        return cwd
    return os.getcwd()


def match_block_reason(command: str) -> str | None:
    for label, pattern in BLOCK_RULES:
        if pattern.search(command):
            return label
    if DELETE_WITHOUT_WHERE.search(command) and not WHERE_CLAUSE.search(command):
        return "DELETE FROM"
    return None


def append_log(log_path: Path, command: str, project_path: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_deny_response(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive bash command: detected `{reason}`. "
                "Use a safer scoped alternative or ask the user before destructive actions."
            ),
        }
    }


def main(
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    log_path: Path | None = None,
) -> int:
    input_stream = stdin or sys.stdin
    output_stream = stdout or sys.stdout
    resolved_log_path = log_path or default_log_path()

    payload = parse_payload(input_stream.read())
    command = extract_command(payload)
    if not command:
        return 0

    reason = match_block_reason(command)
    if reason is None:
        return 0

    project_path = extract_project_path(payload)
    append_log(resolved_log_path, command, project_path)
    output_stream.write(json.dumps(build_deny_response(reason), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
