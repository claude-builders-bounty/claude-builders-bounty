#!/usr/bin/env python3
"""Claude Code PreToolUse hook — block destructive bash before execution.

Install:
  mkdir -p ~/.claude/hooks
  cp block-destructive.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/block-destructive.py

Wire in ~/.claude/settings.json (or project .claude/settings.json):

{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "rm -rf (recursive force delete)",
        re.compile(r"\brm\s+(-[^\s]*f[^\s]*r|-[^\s]*r[^\s]*f)\b", re.I),
    ),
    ("rm -rf (recursive force delete)", re.compile(r"\brm\s+-rf\b|\brm\s+-fr\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b.*(--force\b|-f\b)", re.I)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\s+(table\s+)?\w+", re.I)),
]


def is_delete_without_where(command: str) -> bool:
    if not re.search(r"\bdelete\s+from\b", command, re.I):
        return False
    return not re.search(r"\bdelete\s+from\b[\s\S]*?\bwhere\b", command, re.I)


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "bash", "script"):
            val = tool_input.get(key)
            if isinstance(val, str) and val.strip():
                return val
    return json.dumps(payload)


def log_block(command: str, reason: str, project: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\tproject={project}\treason={reason}\tcmd={command.replace(chr(9), ' ')}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def deny(command: str, reason: str, project: str) -> int:
    log_block(command, reason, str(project))
    msg = (
        f"BLOCKED destructive bash ({reason}).\n"
        f"Command: {command}\n"
        f"Logged to {LOG_PATH}. Ask the user to run this manually if intentional."
    )
    print(msg, file=sys.stderr)
    print(json.dumps({"decision": "block", "reason": msg}))
    return 2


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {"raw": raw}

    command = extract_command(payload)
    project = (
        payload.get("cwd")
        or payload.get("workspace_dir")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    if is_delete_without_where(command):
        return deny(command, "DELETE FROM without WHERE", project)

    for reason, pattern in BLOCK_RULES:
        if pattern.search(command):
            return deny(command, reason, project)

    print(json.dumps({"decision": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
