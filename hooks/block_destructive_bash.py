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


DEFAULT_DENY_RULES = [
    {
        "name": "recursive forced removal",
        "pattern": r"(?is)(^|[;&|]\s*)(?:sudo\s+|command\s+)?rm\s+(?=[^\n;&|]*?(?:-[^\s]*r[^\s]*\b|--recursive\b))(?=[^\n;&|]*?(?:-[^\s]*f[^\s]*\b|--force\b))",
    },
    {
        "name": "forced git push",
        "pattern": r"(?is)(^|[;&|]\s*)git\s+(?:-[A-Za-z]\s+\S+\s+)*push\b[^\n;|&]*(?:--force(?:-with-lease)?\b|(?:^|\s)-f(?:\s|$))",
    },
]


DEFAULT_ALLOW_RULES: list[dict[str, str]] = []
DATABASE_CLIENTS = {
    "duckdb",
    "mariadb",
    "mysql",
    "psql",
    "sqlite3",
}
SQL_START_RE = re.compile(r"(?is)^\s*(?:DROP\s+TABLE|TRUNCATE|DELETE\s+FROM)\b")


def load_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        event = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Destructive command hook could not parse JSON input: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(event, dict):
        print("Destructive command hook expected a JSON object from Claude Code.", file=sys.stderr)
        sys.exit(2)
    return event


def normalize_rules(raw_rules: Any, default: list[dict[str, str]]) -> list[dict[str, str]]:
    if raw_rules is None:
        return list(default)
    if not isinstance(raw_rules, list):
        raise ValueError("rules must be a list")

    rules: list[dict[str, str]] = []
    for index, rule in enumerate(raw_rules):
        if isinstance(rule, str):
            rules.append({"name": rule, "pattern": rule})
            continue
        if isinstance(rule, dict) and isinstance(rule.get("pattern"), str):
            rules.append({"name": str(rule.get("name") or f"rule {index + 1}"), "pattern": rule["pattern"]})
            continue
        raise ValueError(f"rule {index + 1} must be a string or object with a pattern")
    return rules


def load_config() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    config_path = os.environ.get("DESTRUCTIVE_BASH_HOOK_CONFIG")
    if not config_path:
        return list(DEFAULT_DENY_RULES), list(DEFAULT_ALLOW_RULES)

    path = Path(config_path).expanduser()
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"config file does not exist: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"config file is not valid JSON: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError("config file must contain a JSON object")

    deny = normalize_rules(config.get("deny"), DEFAULT_DENY_RULES)
    allow = normalize_rules(config.get("allow"), DEFAULT_ALLOW_RULES)
    return deny, allow


def get_tool_name(event: dict[str, Any]) -> str:
    for key in ("tool_name", "toolName", "name"):
        value = event.get(key)
        if isinstance(value, str):
            return value
    return ""


def get_command(event: dict[str, Any]) -> str | None:
    candidates = [
        event.get("tool_input"),
        event.get("toolInput"),
        event.get("input"),
        event.get("parameters"),
        event,
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and isinstance(candidate.get("command"), str):
            return candidate["command"]
    return None


def get_project_path(event: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath", "workspace", "workspace_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def delete_from_without_where(command: str) -> bool:
    statements = re.split(r";|\n", command, flags=re.IGNORECASE)
    for statement in statements:
        if re.search(r"(?is)\bDELETE\s+FROM\b", statement) and not re.search(r"(?is)\bWHERE\b", statement):
            return True
    return False


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return []


def includes_database_client(command: str) -> bool:
    words = shell_words(command)
    for word in words:
        binary = Path(word).name.lower()
        if binary in DATABASE_CLIENTS:
            return True
    return bool(re.search(r"(?is)(?:^|[|;&]\s*)(?:psql|mysql|mariadb|sqlite3|duckdb)\b", command))


def should_inspect_sql(command: str) -> bool:
    return bool(SQL_START_RE.search(command)) or includes_database_client(command)


def destructive_sql_reason(command: str) -> str | None:
    if not should_inspect_sql(command):
        return None
    if re.search(r"(?is)\bDROP\s+TABLE\b", command):
        return "drop table statement"
    if re.search(r"(?is)\bTRUNCATE\b", command):
        return "truncate statement"
    if delete_from_without_where(command):
        return "DELETE FROM without a WHERE clause"
    return None


def match_rule(command: str, rules: list[dict[str, str]]) -> str | None:
    for rule in rules:
        try:
            if re.search(rule["pattern"], command):
                return rule["name"]
        except re.error as exc:
            print(f"Ignoring invalid destructive command hook regex {rule['name']!r}: {exc}", file=sys.stderr)
    return None


def append_block_log(command: str, project_path: str, reason: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def block(command: str, project_path: str, reason: str) -> int:
    append_block_log(command, project_path, reason)
    message = (
        "Blocked destructive Bash command before execution.\n"
        f"Reason: {reason}\n"
        f"Project: {project_path}\n"
        "The attempted command was logged to ~/.claude/hooks/blocked.log."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": message,
                }
            }
        )
    )
    return 0


def main() -> int:
    event = load_event()
    tool_name = get_tool_name(event)
    command = get_command(event)
    if tool_name and tool_name.lower() != "bash":
        return 0
    if not command:
        return 0

    try:
        deny_rules, allow_rules = load_config()
    except ValueError as exc:
        print(f"Destructive command hook configuration error: {exc}", file=sys.stderr)
        return 2

    allowed = match_rule(command, allow_rules)
    if allowed:
        return 0

    denied = match_rule(command, deny_rules)
    if denied:
        return block(command, get_project_path(event), denied)

    destructive_sql = destructive_sql_reason(command)
    if destructive_sql:
        return block(command, get_project_path(event), destructive_sql)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
