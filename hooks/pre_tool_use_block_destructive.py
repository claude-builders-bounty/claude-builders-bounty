#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks high-risk Bash commands.

The hook reads the Claude Code hook payload from stdin. It exits with code 2
and writes a clear message to stderr when a command should be blocked.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "recursive force remove",
        re.compile(r"(?:^|[;&|\s])(?:sudo\s+)?rm\s+(?:(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*)|(?:-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)|(?:--recursive\s+--force)|(?:--force\s+--recursive))(?:\s|$)", re.I),
        "rm with recursive force flags can delete large parts of a project or system.",
    ),
    (
        "drop table",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE can permanently remove database structure and data.",
    ),
    (
        "truncate table",
        re.compile(r"\btruncate(?:\s+table)?\b", re.I),
        "TRUNCATE can remove all rows from a table without a normal row-by-row safety check.",
    ),
    (
        "force push",
        re.compile(r"\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?\b|-f\b)", re.I),
        "Force-pushing can rewrite shared Git history.",
    ),
)

DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.I)
WHERE_AFTER_DELETE = re.compile(r"\bdelete\s+from\b.*\bwhere\b", re.I | re.S)


def load_payload(stdin_text: str) -> dict[str, Any]:
    if not stdin_text.strip():
        return {}
    try:
        payload = json.loads(stdin_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Could not parse Claude hook JSON payload: {exc}") from exc
    if not isinstance(payload, dict):
        return {}
    return payload


def command_from_payload(payload: dict[str, Any]) -> str:
    if payload.get("tool_name") != "Bash":
        return ""
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command", "")
    return command if isinstance(command, str) else ""


def project_path_from_payload(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd") or payload.get("project_path")
    return str(cwd) if cwd else os.getcwd()


def blocked_reason(command: str) -> tuple[str, str] | None:
    for name, pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            return name, reason

    if DELETE_FROM.search(command) and not WHERE_AFTER_DELETE.search(command):
        return (
            "delete without where",
            "DELETE FROM without a WHERE clause can remove every row in a table.",
        )

    return None


def log_blocked_attempt(command: str, project_path: str, rule_name: str) -> Path:
    log_path = Path(os.environ.get("CLAUDE_HOOK_LOG_PATH", DEFAULT_LOG_PATH)).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "rule": rule_name,
        "command": command,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return log_path


def install_settings(script_path: Path) -> Path:
    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to edit invalid JSON at {settings_path}: {exc}") from exc
    else:
        settings = {}

    if not isinstance(settings, dict):
        raise SystemExit(f"Refusing to edit non-object JSON at {settings_path}")

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    command_entry = {
        "type": "command",
        "command": sys.executable,
        "args": [str(script_path.resolve())],
    }
    matcher_entry = {"matcher": "Bash", "hooks": [command_entry]}

    already_present = False
    for item in pre_tool_use:
        if not isinstance(item, dict):
            continue
        if item.get("matcher") != "Bash":
            continue
        item_hooks = item.get("hooks", [])
        if command_entry in item_hooks:
            already_present = True
            break

    if not already_present:
        pre_tool_use.append(matcher_entry)
        settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return settings_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Bash commands before Claude Code runs them.")
    parser.add_argument("--install-settings", action="store_true", help="Add this hook to ~/.claude/settings.json for Bash PreToolUse events.")
    args = parser.parse_args()

    if args.install_settings:
        settings_path = install_settings(Path(__file__))
        print(f"Claude Code settings updated: {settings_path}")
        return 0

    payload = load_payload(sys.stdin.read())
    command = command_from_payload(payload)
    if not command:
        return 0

    reason = blocked_reason(command)
    if reason is None:
        return 0

    rule_name, explanation = reason
    project_path = project_path_from_payload(payload)
    log_path = log_blocked_attempt(command, project_path, rule_name)

    print(
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {explanation}\n"
        f"Project: {project_path}\n"
        f"Log: {log_path}\n"
        "Use a safer, narrower command or ask for explicit human review before continuing.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
