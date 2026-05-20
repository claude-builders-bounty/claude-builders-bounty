#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path


HOOK_NAME = "destructive-bash-guard.py"
BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


class BlockReason:
    def __init__(self, pattern: str, reason: str) -> None:
        self.pattern = pattern
        self.reason = reason


def strip_single_and_double_quoted_text(command: str) -> str:
    """Remove quoted strings so examples like echo 'rm -rf /' are not blocked."""
    result: list[str] = []
    quote: str | None = None
    escaped = False

    for char in command:
        if escaped:
            escaped = False
            if quote is None:
                result.append(" ")
            continue

        if char == "\\":
            escaped = True
            if quote is None:
                result.append(char)
            continue

        if quote:
            if char == quote:
                quote = None
            continue

        if char in {"'", '"'}:
            quote = char
            result.append(" ")
            continue

        result.append(char)

    return "".join(result)


def strip_sql_string_literals(command: str) -> str:
    return re.sub(r"'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", " ", command)


def sql_text_for_detection(command: str) -> str:
    db_clients = {
        "psql",
        "mysql",
        "sqlite3",
        "duckdb",
        "clickhouse-client",
        "sqlcmd",
    }

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    token_basenames = {Path(token).name for token in tokens}
    if token_basenames.intersection(db_clients):
        return " ".join(tokens)

    if re.match(r"^\s*(drop\s+table|truncate|delete\s+from)\b", command, flags=re.IGNORECASE):
        return command

    return ""


def has_delete_without_where(command: str) -> bool:
    sql = strip_sql_string_literals(sql_text_for_detection(command))
    for statement in re.split(r";|\n", sql, flags=re.MULTILINE):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, flags=re.IGNORECASE
        ):
            return True
    return False


def detect_block_reason(command: str) -> BlockReason | None:
    shell = strip_single_and_double_quoted_text(command)
    sql = sql_text_for_detection(command)

    shell_checks: list[tuple[str, str, str]] = [
        (
            r"(^|[;&|()\s])rm\s+(?:-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)(?=\s|$)",
            "rm -rf",
            "recursive forced removal is blocked",
        ),
        (
            r"(^|[;&|()\s])git\s+push\b[^\n;&|]*\s--force(?:-with-lease)?(?:\s|$)",
            "git push --force",
            "force-pushing is blocked",
        ),
    ]

    for regex, pattern, reason in shell_checks:
        if re.search(regex, shell, flags=re.IGNORECASE):
            return BlockReason(pattern, reason)

    sql_checks: list[tuple[str, str, str]] = [
        (r"\bdrop\s+table\b", "DROP TABLE", "dropping database tables is blocked"),
        (r"\btruncate\b", "TRUNCATE", "truncating database tables is blocked"),
    ]

    for regex, pattern, reason in sql_checks:
        if sql and re.search(regex, sql, flags=re.IGNORECASE):
            return BlockReason(pattern, reason)

    if has_delete_without_where(command):
        return BlockReason("DELETE FROM without WHERE", "unbounded SQL deletes are blocked")

    return None


def project_path(payload: dict) -> str:
    return str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def log_blocked_attempt(command: str, payload: dict, reason: BlockReason) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path(payload),
        "pattern": reason.pattern,
        "attempted_command": command,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, separators=(",", ":")) + "\n")


def deny(reason: BlockReason) -> None:
    message = (
        f"Blocked destructive Bash command: {reason.pattern}. "
        f"Reason: {reason.reason}. Rewrite the command to be scoped, reversible, "
        "or ask the user for explicit confirmation."
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


def run_hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-bash-guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = detect_block_reason(command)
    if not reason:
        return 0

    log_blocked_attempt(command, payload, reason)
    deny(reason)
    return 0


def install() -> int:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / HOOK_NAME
    shutil.copy2(Path(__file__), target)
    target.chmod(0o755)

    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Refusing to edit invalid JSON at {settings_path}: {exc}", file=sys.stderr)
            return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    hook_group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": str(target),
            }
        ],
    }

    if not any(group == hook_group for group in pre_tool_use):
        pre_tool_use.append(hook_group)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed {target}")
    print(f"Updated {settings_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="install into ~/.claude/hooks and update settings")
    args = parser.parse_args()

    if args.install:
        return install()

    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
