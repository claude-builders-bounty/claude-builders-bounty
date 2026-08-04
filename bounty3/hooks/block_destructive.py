#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Install (2 commands) — see README.md.
Reads JSON from stdin (Claude Code hook protocol). Exit non-zero to block.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that must never run unsupervised
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "recursive force remove",
        re.compile(r"(^|[;&|]\s*)rm\s+(-[^\s]*r[^\s]*f|-rf|-fr)\b", re.I),
    ),
    ("DROP TABLE", re.compile(r"\bDROP\s+TABLE\b", re.I)),
    ("git push force", re.compile(r"\bgit\s+push\b[^\n]*--force\b", re.I)),
    ("TRUNCATE", re.compile(r"\bTRUNCATE\s+(TABLE\s+)?\w+", re.I)),
    (
        "DELETE without WHERE",
        re.compile(
            r"\bDELETE\s+FROM\s+\S+(?!\s+WHERE\b)(?=\s*;|\s*$|\s*[;&|])",
            re.I,
        ),
    ),
]


def extract_command(payload: dict) -> str:
    inp = (
        payload.get("tool_input")
        or payload.get("toolInput")
        or payload.get("input")
        or {}
    )
    if isinstance(inp, str):
        try:
            inp = json.loads(inp)
        except Exception:
            return inp
    if not isinstance(inp, dict):
        return str(inp)
    for key in ("command", "cmd", "bash", "script"):
        if key in inp and inp[key]:
            return str(inp[key])
    return json.dumps(inp)


def log_block(command: str, reason: str, project: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"{datetime.now(timezone.utc).isoformat()}\t{reason}\t"
        f"project={project}\tcmd={command.replace(chr(9), ' ')}\n"
    )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw": raw}

    tool = (
        payload.get("tool_name")
        or payload.get("toolName")
        or payload.get("tool")
        or ""
    ).lower()
    if tool and tool not in {"bash", "shell", "run_terminal_cmd", "terminal"}:
        return 0

    command = extract_command(payload)
    project = (
        payload.get("cwd")
        or payload.get("workspace_roots")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    if isinstance(project, list):
        project = ",".join(map(str, project))

    for reason, pat in RULES:
        if pat.search(command or ""):
            log_block(command, reason, str(project))
            msg = (
                f"BLOCKED by pre-tool-use safety hook: matched '{reason}'.\n"
                f"Command: {command}\n"
                f"Logged to {LOG}. Use a safer alternative or run manually "
                f"with explicit human approval."
            )
            print(msg, file=sys.stderr)
            print(json.dumps({"decision": "block", "reason": msg}))
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
