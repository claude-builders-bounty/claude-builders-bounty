#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_PATH = HOOKS_DIR / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


class Rule:
    def __init__(self, name: str, reason: str, pattern: str) -> None:
        self.name = name
        self.reason = reason
        self.pattern = re.compile(pattern, re.IGNORECASE | re.DOTALL)

    def matches(self, command: str) -> bool:
        return bool(self.pattern.search(strip_comments(command)))


RULES = [
    Rule(
        "rm -rf",
        "recursive force delete can irreversibly remove project or system files",
        r"(^|[;&|]\s*)rm\s+(?=[^\n;&|]*-[A-Za-z]*r)(?=[^\n;&|]*-[A-Za-z]*f)[^\n;&|]*",
    ),
    Rule(
        "DROP TABLE",
        "DROP TABLE removes database schema and data",
        r"\bdrop\s+table\b",
    ),
    Rule(
        "TRUNCATE",
        "TRUNCATE removes table data without row-level review",
        r"\btruncate(?:\s+table)?\b",
    ),
    Rule(
        "git push --force",
        "force-pushing can rewrite shared branch history",
        r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)\b",
    ),
]


def strip_comments(command: str) -> str:
    lines = []
    for line in command.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        lines.append(line)
    return "\n".join(lines)


def delete_without_where(command: str) -> bool:
    cleaned = strip_comments(command)
    statements = re.split(r";|\n", cleaned)
    for statement in statements:
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE):
            if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
                return True
    return False


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
        return str(command)
    return ""


def is_bash_tool(payload: dict[str, Any]) -> bool:
    tool_name = payload.get("tool_name") or payload.get("tool") or payload.get("name")
    return str(tool_name).lower() in {"bash", "shell"}


def project_path(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        cwd = tool_input.get("cwd") or tool_input.get("workdir")
        if cwd:
            return str(cwd)
    return str(payload.get("cwd") or os.getcwd())


def blocked_reason(command: str) -> tuple[str, str] | None:
    for rule in RULES:
        if rule.matches(command):
            return rule.name, rule.reason
    if delete_without_where(command):
        return "DELETE FROM without WHERE", "DELETE FROM without WHERE can erase every row in a table"
    return None


def log_block(command: str, path: str, rule: str, reason: str) -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "command": command,
        "project_path": path,
        "rule": rule,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, separators=(",", ":")) + "\n")


def deny(rule: str, reason: str, log_path: Path) -> None:
    message = (
        f"Blocked destructive Bash command ({rule}). {reason}. "
        f"The attempt was logged to {log_path}."
    )
    print(json.dumps({"decision": "block", "reason": message}))


def install() -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = "python ~/.claude/hooks/destructive-command-blocker.py"
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command}],
    }
    if entry not in pre_tool_use:
        pre_tool_use.append(entry)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed PreToolUse hook in {SETTINGS_PATH}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install", action="store_true", help="add hook entry to ~/.claude/settings.json")
    args = parser.parse_args()

    if args.install:
        install()
        return 0

    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict) or not is_bash_tool(payload):
        return 0

    command = extract_command(payload)
    if not command:
        return 0

    block = blocked_reason(command)
    if block is None:
        return 0

    rule, reason = block
    path = project_path(payload)
    log_block(command, path, rule, reason)
    deny(rule, reason, LOG_PATH)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
