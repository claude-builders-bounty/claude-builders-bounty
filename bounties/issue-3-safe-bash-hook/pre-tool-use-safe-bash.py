#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BLOCKERS = [
    (re.compile(r"\brm\s+(?:-[^\s]*r[^\s]*f|- [^\s]*r[^\s]*f|-[^\s]*f[^\s]*r)\b"), "recursive force removal"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=)", re.IGNORECASE), "force push"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE"),
]


def command_from(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return ""


def main() -> int:
    payload = json.load(sys.stdin)
    command = command_from(payload)
    project = os.getcwd()
    for pattern, reason in BLOCKERS:
        if pattern.search(command):
            log = Path.home() / ".claude" / "hooks" / "blocked.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(
                log.read_text() if log.exists() else "",
                encoding="utf-8",
            )
            with log.open("a", encoding="utf-8") as fh:
                fh.write(f"{datetime.now(timezone.utc).isoformat()}\t{project}\t{command}\n")
            print(f"Blocked dangerous bash command ({reason}). Review it manually before running.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
