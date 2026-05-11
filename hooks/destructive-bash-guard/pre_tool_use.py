#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm-rf",
        re.compile(r"(^|[;&|]\s*)rm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-+[A-Za-z]*f[A-Za-z]*r)\b", re.IGNORECASE),
        "Recursive force deletion can remove files irreversibly.",
    ),
    (
        "drop-table",
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "DROP TABLE can permanently destroy database schema and data.",
    ),
    (
        "drop-database",
        re.compile(r"\bdrop\s+database\b", re.IGNORECASE),
        "DROP DATABASE can permanently destroy an entire database.",
    ),
    (
        "truncate",
        re.compile(r"\btruncate(?:\s+table)?\b", re.IGNORECASE),
        "TRUNCATE removes table data without row-level safeguards.",
    ),
)


def get_tool_name(payload: dict[str, Any]) -> str:
    return str(payload.get("tool_name") or payload.get("name") or "")


def get_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    tool_input = payload.get("tool_input") or payload.get("input") or payload.get("arguments") or {}
    return tool_input if isinstance(tool_input, dict) else {}


def get_command(payload: dict[str, Any]) -> str:
    tool_input = get_tool_input(payload)
    command = tool_input.get("command") or tool_input.get("cmd") or payload.get("command")
    return command if isinstance(command, str) else ""


def get_project_path(payload: dict[str, Any]) -> str:
    tool_input = get_tool_input(payload)
    candidates = (
        tool_input.get("cwd"),
        payload.get("cwd"),
        payload.get("project_dir"),
        payload.get("workspace_dir"),
        os.environ.get("CLAUDE_PROJECT_DIR"),
        os.getcwd(),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return ""


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return re.sub(r"--[^\n\r]*", " ", sql)


def has_delete_without_where(command: str) -> bool:
    cleaned = strip_sql_comments(command)
    for match in re.finditer(r"\bdelete\s+from\b", cleaned, flags=re.IGNORECASE):
        statement_tail = cleaned[match.end() :].split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return True
    return False


def has_force_push(command: str) -> bool:
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()

    if len(tokens) < 3:
        return False

    for index, token in enumerate(tokens[:-2]):
        if token == "git" and tokens[index + 1] == "push":
            push_args = tokens[index + 2 :]
            return any(
                arg == "-f"
                or arg == "--force"
                or arg.startswith("--force=")
                or arg == "--force-with-lease"
                or arg.startswith("--force-with-lease=")
                for arg in push_args
            )
    return False


def find_violation(command: str) -> tuple[str, str] | None:
    for rule_name, pattern, reason in RULES:
        if pattern.search(command):
            return rule_name, reason

    if has_force_push(command):
        return "git-force-push", "Force-pushing can overwrite remote history."

    if has_delete_without_where(command):
        return "delete-without-where", "DELETE FROM without WHERE can remove every row in a table."

    return None


def log_block(payload: dict[str, Any], command: str, rule: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": get_project_path(payload),
        "rule": rule,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def allow() -> dict[str, Any]:
    return {"continue": True, "suppressOutput": True}


def deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    if get_tool_name(payload) != "Bash":
        return allow()

    command = get_command(payload)
    if not command:
        return allow()

    violation = find_violation(command)
    if not violation:
        return allow()

    rule, reason = violation
    log_block(payload, command, rule, reason)
    return deny(
        f"Blocked destructive Bash command ({rule}): {reason} "
        f"The attempted command was logged to {LOG_PATH}."
    )


def print_settings() -> None:
    print(json.dumps(settings_entry(), indent=2))


def settings_entry() -> dict[str, Any]:
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "~/.claude/hooks/destructive-bash-guard.py",
                        }
                    ],
                }
            ]
        }
    }


def install_settings(settings_path: Path | None = None) -> Path:
    path = settings_path or (Path.home() / ".claude" / "settings.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            settings = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to modify invalid JSON in {path}: {exc}") from exc
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    entry = settings_entry()["hooks"]["PreToolUse"][0]
    command = entry["hooks"][0]["command"]

    for existing in pre_tool_use:
        if (
            isinstance(existing, dict)
            and existing.get("matcher") == "Bash"
            and any(isinstance(hook, dict) and hook.get("command") == command for hook in existing.get("hooks", []))
        ):
            break
    else:
        pre_tool_use.append(entry)

    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-settings", action="store_true", help="print a Claude Code settings snippet")
    parser.add_argument("--install", action="store_true", help="merge the hook into ~/.claude/settings.json")
    args = parser.parse_args()

    if args.print_settings:
        print_settings()
        return 0

    if args.install:
        path = install_settings()
        print(f"Installed destructive Bash guard in {path}")
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps(deny(f"Invalid hook JSON input: {exc}")))
        return 0

    print(json.dumps(evaluate(payload)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
