#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive Bash / SQL commands.

Reads Claude Code hook JSON from stdin. On match, denies the tool call and
logs to ~/.claude/hooks/blocked.log.

Stdlib only — no third-party dependencies.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_PATH = HOOK_DIR / "blocked.log"

_DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
_TRUNCATE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)
_GIT_FORCE_PUSH = re.compile(
    r"\bgit\s+push\b[^;\n|&]*?(?:--force\b|--force-with-lease\b|(?<![\w-])-f(?![\w-]))",
    re.IGNORECASE,
)
_STMT_SPLIT = re.compile(r";(?=(?:[^'\"]|'[^']*'|\"[^\"]*\")*$)")
_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
_HAS_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)

# Split shell into rough statements on ; & | newlines / && / ||
_SHELL_SPLIT = re.compile(r"(?:&&|\|\||[;&|\n])")


def _is_rm_rf(statement: str) -> bool:
    """True if statement looks like `rm` with both recursive and force flags."""
    # Find an `rm` command word (optional sudo), not part of another word
    m = re.search(r"(?:^|[\s(`])(?:sudo\s+)?rm\b(.*)$", statement, re.IGNORECASE)
    if not m:
        return False
    args = m.group(1)
    # Combined short flags: -rf, -fr, -Rf, -frv, etc.
    if re.search(r"(?<![\w-])-\w*[rR]\w*[fF]\w*(?!\w)", args) or re.search(
        r"(?<![\w-])-\w*[fF]\w*[rR]\w*(?!\w)", args
    ):
        return True
    has_r = bool(
        re.search(r"(?<![\w-])-\w*[rR]\w*(?!\w)", args)
        or re.search(r"(?<![\w-])--recursive\b", args, re.IGNORECASE)
    )
    has_f = bool(
        re.search(r"(?<![\w-])-\w*[fF]\w*(?!\w)", args)
        or re.search(r"(?<![\w-])--force\b", args, re.IGNORECASE)
    )
    return has_r and has_f


def _check_delete_without_where(command: str) -> Optional[Tuple[str, str]]:
    for stmt in _STMT_SPLIT.split(command):
        stmt = stmt.strip()
        if not stmt:
            continue
        if _DELETE_FROM.search(stmt) and not _HAS_WHERE.search(stmt):
            return (
                "DELETE FROM without WHERE",
                "Blocked DELETE FROM without a WHERE clause — this would delete all rows. "
                "Add a WHERE filter, or run the deletion manually outside Claude Code.",
            )
    return None


def detect(command: str) -> Optional[Tuple[str, str]]:
    """Return (label, reason) if the command should be blocked."""
    if not command or not str(command).strip():
        return None
    command = str(command)

    for part in _SHELL_SPLIT.split(command):
        if _is_rm_rf(part):
            return (
                "rm -rf",
                "Blocked recursive force-delete (rm -rf / equivalent). "
                "This can wipe large parts of the filesystem. Remove files more specifically, "
                "or run the deletion yourself outside Claude Code.",
            )

    if _DROP_TABLE.search(command):
        return (
            "DROP TABLE",
            "Blocked DROP TABLE — this permanently destroys a database table. "
            "Confirm and run the DDL yourself if you truly intend to drop it.",
        )

    if _TRUNCATE.search(command):
        return (
            "TRUNCATE",
            "Blocked TRUNCATE — this empties a table without a row filter. "
            "Use a targeted DELETE with WHERE, or run TRUNCATE yourself outside Claude Code.",
        )

    if _GIT_FORCE_PUSH.search(command):
        return (
            "git push --force",
            "Blocked git push --force / -f — force-push rewrites remote history. "
            "Push without --force, or force-push yourself after reviewing the ref.",
        )

    return _check_delete_without_where(command)


def _project_path(payload: dict) -> str:
    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    return str(cwd)


def log_blocked(command: str, project: str, label: str) -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts} | {label} | {project} | {command}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def deny_response(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0

    tool_name = payload.get("tool_name") or ""
    if tool_name and tool_name != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if isinstance(command, list):
        command = " ".join(str(c) for c in command)

    hit = detect(str(command))
    if not hit:
        return 0

    label, reason = hit
    project = _project_path(payload)
    try:
        log_blocked(str(command), project, label)
    except OSError as exc:
        reason = f"{reason} (also failed to write blocked.log: {exc})"

    print(json.dumps(deny_response(reason), ensure_ascii=False))
    print(reason, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
