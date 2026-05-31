#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


BLOCK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "recursive-force-delete",
        re.compile(r"(^|[;&|]\s*)rm\s+(-[A-Za-z]*r[A-Za-z]*f|- [^\n]*|-[A-Za-z]*f[A-Za-z]*r)\b"),
        "Blocks rm commands that combine recursive and force deletion.",
    ),
    (
        "drop-table",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "Blocks SQL DROP TABLE statements.",
    ),
    (
        "truncate",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "Blocks SQL TRUNCATE statements.",
    ),
    (
        "force-push",
        re.compile(r"\bgit\s+push\b[^\n]*(--force|-f\b)", re.IGNORECASE),
        "Blocks force pushes.",
    ),
    (
        "delete-without-where",
        re.compile(r"\bDELETE\s+FROM\s+[\w.\"`\[\]-]+(?:(?!\bWHERE\b).)*;?\s*$", re.IGNORECASE | re.DOTALL),
        "Blocks DELETE FROM statements that do not include a WHERE clause.",
    ),
]


def extract_command(payload: dict[str, Any]) -> str:
    for key in ("command", "cmd", "input"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "input"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "repo_path"):
        value = payload.get(key)
        if isinstance(value, str):
            return value
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("cwd", "project_path", "workspace", "repo_path"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return str(Path.cwd())


def blocked_reason(command: str) -> tuple[str, str] | None:
    for rule_name, pattern, description in BLOCK_RULES:
        if pattern.search(command):
            return rule_name, description
    return None


def append_log(log_path: Path, command: str, project_path: str, rule_name: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "rule": rule_name,
        "project_path": project_path,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_payload(raw: str) -> dict[str, Any]:
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {"command": raw}
    return payload if isinstance(payload, dict) else {}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Block destructive bash commands for Claude Code hooks.")
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--command", help="Command to inspect. If omitted, JSON is read from stdin.")
    parser.add_argument("--project-path", help="Project path to record in blocked.log.")
    args = parser.parse_args(argv)

    if args.command is not None:
        command = args.command
        project_path = args.project_path or str(Path.cwd())
    else:
        payload = load_payload(sys.stdin.read())
        command = extract_command(payload)
        project_path = args.project_path or extract_project_path(payload)

    reason = blocked_reason(command)
    if reason is None:
        print(json.dumps({"decision": "allow"}))
        return 0

    rule_name, description = reason
    append_log(args.log, command, project_path, rule_name)
    print(
        json.dumps(
            {
                "decision": "block",
                "reason": f"{description} Rule: {rule_name}.",
                "message": "Command blocked before execution because it matches a destructive pattern.",
            }
        )
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
