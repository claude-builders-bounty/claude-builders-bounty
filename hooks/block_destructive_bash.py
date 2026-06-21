#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCKED_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive force delete",
        re.compile(r"(^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*[rR][A-Za-z]*[fF]|-[A-Za-z]*[fF][A-Za-z]*[rR])\b"),
        "rm -rf can recursively destroy project or system files.",
    ),
    (
        "sql drop table",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE removes an entire database table.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;&|]*\s--force(?:-with-lease)?\b"),
        "git push --force can overwrite remote history.",
    ),
    (
        "sql truncate",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE removes all rows from a table.",
    ),
    (
        "sql delete without where",
        re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.IGNORECASE),
        "DELETE FROM without a WHERE clause can remove every row.",
    ),
)


def main() -> int:
    payload = read_payload()
    tool_name = str(payload.get("tool_name", ""))
    command = extract_command(payload)

    if tool_name.lower() != "bash" and not command:
        return 0

    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())
    match = first_blocked_rule(command)
    if not match:
        return 0

    rule_name, _, reason = match
    write_block_log(project_path, command, rule_name)

    print(
        "Blocked destructive Bash command before execution.\n"
        f"Rule: {rule_name}\n"
        f"Reason: {reason}\n"
        "Revise the command to use a safer, narrower operation. If this is intentional, "
        "ask the user for explicit approval and run it outside this hook.",
        file=sys.stderr,
    )
    return 2


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Could not parse Claude hook JSON: {exc}", file=sys.stderr)
        return {}
    return parsed if isinstance(parsed, dict) else {}


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or tool_input.get("input")
        return str(command or "")

    if isinstance(tool_input, str):
        return tool_input

    command = payload.get("command")
    return str(command or "")


def first_blocked_rule(command: str) -> tuple[str, re.Pattern[str], str] | None:
    for rule in BLOCKED_RULES:
        if rule[1].search(command):
            return rule
    return None


def write_block_log(project_path: str, command: str, rule_name: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "blocked.log"
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "rule": rule_name,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
