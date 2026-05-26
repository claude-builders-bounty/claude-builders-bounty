#!/usr/bin/env python3
"""Claude Code pre-tool-use hook that blocks destructive bash commands."""
import json, os, re, sys
from datetime import datetime, timezone
from pathlib import Path

BLOCK_RULES = [
    (re.compile(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f|-[A-Za-z]*f[A-Za-z]*r)\b"), "rm -rf can permanently delete files"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE can destroy database schema/data"),
    (re.compile(r"\bgit\s+push\b[^\n;|&]*\s--force(?:\b|=)", re.I), "git push --force can rewrite shared history"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE can delete table contents"),
    (re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.I), "DELETE FROM without WHERE can delete all rows"),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return str(tool_input)


def log_block(command: str, reason: str, project_path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}\t{project_path}\t{reason}\t{command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    command = extract_command(payload)
    project_path = str(payload.get("cwd") or payload.get("project_path") or os.getcwd())

    for pattern, reason in BLOCK_RULES:
        if pattern.search(command):
            log_block(command, reason, project_path)
            print(f"Blocked destructive bash command: {reason}. Review the command and ask for explicit human approval before proceeding.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
