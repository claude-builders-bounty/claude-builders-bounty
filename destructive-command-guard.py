#!/usr/bin/env python3
"""
Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the hook payload from stdin and, when a dangerous command is detected,
emits a Claude Code permissionDecision=deny response. Blocked attempts are
logged as one JSON object per line to ~/.claude/hooks/blocked.log.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple


RM_RF = re.compile(
    r"""(?ix)
    \brm\s+
    (?:
        -[a-z]*r[a-z]*f[a-z]* |
        -[a-z]*f[a-z]*r[a-z]* |
        --recursive(?:\s+--force) |
        --force(?:\s+--recursive)
    )
    (?=\s|$)
    """
)

GIT_FORCE_PUSH = re.compile(
    r"""(?ix)
    \bgit\s+push\b
    [^;&|\n]*
    (?:
        --force(?:-with-lease)? |
        -f
    )
    (?=\s|$)
    """
)

DROP_TABLE = re.compile(r"(?i)\bDROP\s+TABLE\b")
TRUNCATE = re.compile(r"(?i)\bTRUNCATE(?:\s+TABLE)?\b")
DELETE_FROM = re.compile(r"(?i)\bDELETE\s+FROM\b")
WHERE = re.compile(r"(?i)\bWHERE\b")


def _delete_without_where(command: str) -> bool:
    """Return True if any DELETE FROM statement lacks a WHERE clause.

    We inspect the text from each DELETE FROM occurrence until a common SQL/shell
    statement boundary. This intentionally favors safety: a potentially unbounded
    DELETE is blocked rather than guessed safe.
    """
    for match in DELETE_FROM.finditer(command):
        tail = command[match.start():]

        # Stop at a likely statement / shell boundary.
        boundaries = []
        for marker in (";", "\n", "&&", "||"):
            pos = tail.find(marker)
            if pos != -1:
                boundaries.append(pos)
        statement = tail[: min(boundaries)] if boundaries else tail

        if not WHERE.search(statement):
            return True
    return False


def classify(command: str) -> Optional[Tuple[str, str]]:
    """Return (rule, explanation) when command should be blocked."""
    checks = (
        (RM_RF, "rm-rf", "recursive forced deletion (`rm -rf`)"),
        (DROP_TABLE, "drop-table", "SQL table deletion (`DROP TABLE`)"),
        (GIT_FORCE_PUSH, "git-force-push", "forced Git push (`git push --force`)"),
        (TRUNCATE, "truncate", "SQL truncation (`TRUNCATE`)"),
    )

    for pattern, rule, explanation in checks:
        if pattern.search(command):
            return rule, explanation

    if _delete_without_where(command):
        return "delete-without-where", "unbounded SQL deletion (`DELETE FROM` without `WHERE`)"

    return None


def project_path(payload: dict) -> str:
    return str(
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(command: str, project: str, rule: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project,
        "rule": rule,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(response, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        # Fail open for malformed hook input so normal shell usage is not broken.
        return 0

    if payload.get("tool_name") not in (None, "Bash"):
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    result = classify(command)
    if result is None:
        return 0

    rule, explanation = result
    project = project_path(payload)

    try:
        log_block(command, project, rule)
    except OSError:
        # Blocking is more important than logging. Do not allow a destructive
        # command merely because the log file cannot be written.
        pass

    deny(
        "Blocked destructive Bash command: "
        f"{explanation}. Use a safer, scoped alternative or ask the user "
        "for an explicit non-destructive approach."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
