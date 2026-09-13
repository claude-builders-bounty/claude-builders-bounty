#!/usr/bin/env python3
"""PreToolUse hook for Claude Code: intercept and block destructive shell commands.

Usage
-----
1. Save as ``~/.claude/hooks/safeguard.py``
2. ``chmod +x ~/.claude/hooks/safeguard.py``
3. Register under ``hooks.PreToolUse`` with matcher ``Bash`` in Claude Code settings.

Exit codes follow Claude Code hooks:
  0 = allow
  2 = block (stderr is fed back to the model)
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_DIR = Path(os.path.expanduser("~/.claude/hooks"))
LOG_FILE = HOOK_DIR / "safeguard-blocked.log"


def _load_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def _command(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    if isinstance(tool_input, str):
        return tool_input
    return ""


def _cwd(payload: dict) -> str:
    return payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


# (compiled pattern, human-readable reason)
RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)+", re.I), "recursive/force rm"),
    (re.compile(r"\bgit\s+push\b[^\n]*--force(?:-with-lease)?", re.I), "force push"),
    (re.compile(r"\bgit\s+push\b[^\n]*(?:^|\s)-f(?:\s|$)", re.I), "force push -f"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.I), "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f", re.I), "git clean -f"),
    (re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.I), "SQL DROP"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.I), "SQL TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b(?![^;\n]*\bWHERE\b)", re.I), "SQL DELETE without WHERE"),
    (re.compile(r"\bmkfs\.\w+", re.I), "mkfs format"),
    (re.compile(r"\bdd\b[^\n]*of=/dev/", re.I), "dd write to device"),
    (re.compile(r">\s*/dev/(?:sd|nvme|hd)[a-z0-9]*", re.I), "redirect to block device"),
    (re.compile(r"\b(?:shutdown|reboot|halt)\b", re.I), "power command"),
    (re.compile(r"\bchmod\s+-R\s+777\b", re.I), "chmod -R 777"),
    (re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", re.I), "fork bomb"),
    (re.compile(r"\b(?:curl|wget)\b[^\n]*\|\s*(?:ba|z|da)?sh\b", re.I), "pipe remote script to shell"),
    (re.compile(r"\bcrontab\s+-r\b", re.I), "crontab -r"),
    (re.compile(r"\bkill\s+-9\s+1\b", re.I), "kill PID 1"),
]


def _append_log(reason: str, command: str, cwd: str) -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(f"{stamp}\t{reason}\t{cwd}\t{command}\n")


def main() -> int:
    payload = _load_payload()
    command = _command(payload)
    cwd = _cwd(payload)

    if not command:
        return 0

    for pattern, reason in RULES:
        if pattern.search(command):
            _append_log(reason, command, cwd)
            sys.stderr.write(
                "safeguard BLOCKED destructive command ({reason}).\n"
                "A safer rewrite is required, or ask the user to run it manually.\n"
                "Log: {log}\n".format(reason=reason, log=LOG_FILE)
            )
            return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
