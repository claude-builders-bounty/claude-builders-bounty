#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — blocks destructive bash commands before execution.

Reads the hook payload (JSON) from stdin, inspects Bash tool commands, and:
  * exits 0  → allow
  * exits 2  → BLOCK (message on stderr is shown to Claude as the reason)

Every blocked attempt is appended to ~/.claude/hooks/blocked.log as:
  <ISO timestamp>\t<reason>\t<command>\t<project path>
"""
from __future__ import annotations
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# (label, compiled regex) — first match blocks. Deliberately conservative:
# require destructive intent, not just a keyword in a benign string.
RULES = [
    ("rm -rf", re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-rf|-fr)\b")),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\s+TABLE\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n]*(\s--force(?!-with-lease)\b|\s-f\b)")),
    ("mkfs", re.compile(r"\bmkfs(\.\w+)?\b")),
    ("dd to device", re.compile(r"\bdd\b[^\n]*\bof=/dev/")),
    ("fork bomb", re.compile(r":\s*\(\s*\)\s*\{.*\}\s*;?\s*:")),
    ("recursive chmod 777", re.compile(r"\bchmod\s+-R\s+777\b")),
]


def find_reason(cmd: str) -> str | None:
    if not cmd:
        return None
    low = cmd.lower()
    # DELETE FROM without a WHERE clause (checked across the whole command)
    if re.search(r"\bdelete\s+from\b", low) and not re.search(r"\bwhere\b", low):
        return "DELETE without WHERE"
    for label, rx in RULES:
        if rx.search(cmd):
            return label
    return None


def log_block(reason: str, cmd: str, project: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().isoformat(timespec='seconds')}\t{reason}\t{cmd}\t{project}\n")
    except Exception:
        pass


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # never break the session on a malformed payload
    tool = payload.get("tool_name") or payload.get("tool") or ""
    if tool != "Bash":
        return 0
    ti = payload.get("tool_input") or payload.get("input") or {}
    cmd = (ti.get("command") if isinstance(ti, dict) else "") or ""
    project = payload.get("cwd") or os.getcwd()
    reason = find_reason(cmd)
    if reason:
        log_block(reason, cmd, project)
        sys.stderr.write(
            f"🛑 BLOCKED by pre-tool-use hook: matched destructive pattern '{reason}'.\n"
            f"Command: {cmd}\n"
            "This command is refused to prevent irreversible damage. "
            "If it is genuinely intended, run it manually outside Claude Code, "
            "or narrow it to a specific path and explain why.\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
