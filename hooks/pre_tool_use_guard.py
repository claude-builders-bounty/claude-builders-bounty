#!/usr/bin/env python3
"""Claude Code PreToolUse guard for risky Bash commands.

The hook reads the JSON payload Claude Code sends on stdin. If the incoming tool
call is not Bash, or the Bash command is allowed, it exits 0. If the command
matches a configured destructive pattern, it writes a clear explanation to stderr,
logs the attempt, and exits 2 so Claude Code blocks the tool call.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockRule:
    name: str
    pattern: re.Pattern[str]
    reason: str

    def matches(self, command: str) -> bool:
        return bool(self.pattern.search(command))


RULES: tuple[BlockRule, ...] = (
    BlockRule(
        name="recursive-force-remove",
        pattern=re.compile(r"(^|[;&|]\s*)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b"),
        reason="recursive forced removal can delete large parts of the project or home directory",
    ),
    BlockRule(
        name="drop-table",
        pattern=re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        reason="dropping tables destroys schema/data and needs explicit human approval",
    ),
    BlockRule(
        name="truncate",
        pattern=re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        reason="truncate removes table data and needs explicit human approval",
    ),
    BlockRule(
        name="force-push",
        pattern=re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?\b|-f\b)"),
        reason="force pushing can rewrite shared history",
    ),
)

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b(?P<tail>[^;\n]*)", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def extract_tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("tool") or payload.get("name") or "")


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    return ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "repo_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd") or tool_input.get("workdir")
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def find_block_reason(command: str) -> tuple[str, str] | None:
    for rule in RULES:
        if rule.matches(command):
            return rule.name, rule.reason

    for match in DELETE_FROM_RE.finditer(command):
        tail = match.group("tail")
        if not WHERE_RE.search(tail):
            return "delete-without-where", "DELETE FROM without a WHERE clause can wipe an entire table"
    return None


def log_blocked_attempt(command: str, project_path: str, rule_name: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    sanitized = " ".join(command.split())
    LOG_PATH.open("a", encoding="utf-8").write(
        json.dumps(
            {
                "timestamp": timestamp,
                "rule": rule_name,
                "project_path": project_path,
                "command": sanitized,
            },
            sort_keys=True,
        )
        + "\n"
    )


def block_message(rule_name: str, reason: str, project_path: str) -> str:
    return (
        "Claude Code pre-tool-use guard blocked this Bash command.\n"
        f"Rule: {rule_name}\n"
        f"Reason: {reason}.\n"
        f"Project path: {project_path}\n"
        "Ask the user for explicit approval or replace it with a safer, narrower command."
    )


def should_inspect_tool(tool_name: str) -> bool:
    normalized = tool_name.lower()
    return normalized in {"bash", "terminal", "shell"} or "bash" in normalized


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"pre-tool-use guard could not parse hook JSON: {exc}", file=sys.stderr)
        return 0

    tool_name = extract_tool_name(payload)
    if not should_inspect_tool(tool_name):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    result = find_block_reason(command)
    if not result:
        return 0

    rule_name, reason = result
    project_path = extract_project_path(payload)
    log_blocked_attempt(command, project_path, rule_name)
    print(block_message(rule_name, reason, project_path), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
