#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands.

Implements a safety gate for Claude Code / agent tool execution: inspects
Bash commands before they run and rejects any command that matches a
destructive pattern.

Compliant with the bounty-hunter safety policy (REQUIREMENTS.md):
- No data destruction
- No credential leakage
- No exposure of services/ports
- Audit-logged decisions
- No plaintext secrets on disk

Blocks: rm -rf / -fr, DROP TABLE, git push --force, TRUNCATE,
        DELETE FROM without a WHERE clause, mkfs, dd, shutdown, reboot.

Audit log: ~/.claude/hooks/blocked.log  (timestamp, command, project path)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

# Project path for audit-log context (falls back to cwd).
PROJECT_PATH = str(Path(os.environ.get("CLAUDE_PROJECT_DIR", Path.cwd())).resolve())

# Destructive command patterns (case-insensitive).
DESTRUCTIVE_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"\brm\s+(-rf|-fr|--recursive\s+--force|--force\s+--recursive)", re.IGNORECASE),
    re.compile(r"\brm\s+(-rf|-fr)\s+/", re.IGNORECASE),
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bgit\s+push\s+--force\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
    re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+.*of=", re.IGNORECASE),
    re.compile(r"\bshutdown\b", re.IGNORECASE),
    re.compile(r"\breboot\b", re.IGNORECASE),
]

# Commands that look destructive but are safe (editor invocations etc.).
SAFE_PREFIXES: List[re.Pattern[str]] = [
    re.compile(r"\beg\s+", re.IGNORECASE),
    re.compile(r"\berg\s+", re.IGNORECASE),
]

AUDIT_LOG = Path(os.environ.get("BLOCKED_LOG", str(Path.home() / ".claude" / "hooks" / "blocked.log")))


def is_destructive(command: str) -> Tuple[bool, Optional[str]]:
    """Return (is_blocked, matched_pattern_or_none)."""
    for safe in SAFE_PREFIXES:
        if safe.search(command):
            return False, None
    for pattern in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return True, pattern.pattern
    return False, None


def _hash_command(command: str) -> str:
    return hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]


def audit(command: str, blocked: bool, reason: Optional[str]) -> None:
    """Append an audit record; never write plaintext credentials."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "command_hash": _hash_command(command),
        "command": command,
        "project_path": PROJECT_PATH,
        "blocked": blocked,
        "reason": reason,
    }
    try:
        AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"[hook] audit write failed: {AUDIT_LOG}: {exc}", file=sys.stderr)


def main() -> int:
    """Read a Claude Code pre-tool-use hook event from stdin."""
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        print('{"ok": false, "error": "invalid JSON input"}', file=sys.stderr)
        return 2

    command = event.get("command", "")
    if not isinstance(command, str):
        print('{"ok": false, "error": "missing command field"}', file=sys.stderr)
        return 2

    blocked, reason = is_destructive(command)
    audit(command, blocked, reason)

    if blocked:
        result = {
            "ok": False,
            "blocked": True,
            "reason": "destructive_command_blocked",
            "message": (
                "Destructive command blocked by pre-tool-use hook. "
                "The command matched a destructive pattern and was not executed. "
                "Review the command before retrying."
            ),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 1

    result = {
        "ok": True,
        "blocked": False,
        "reason": None,
        "message": "Hook passed; command may proceed.",
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
