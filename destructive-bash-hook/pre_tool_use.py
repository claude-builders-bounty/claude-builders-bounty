#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash before it runs."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF = re.compile(r"(^|[\s;&|])rm\s+(-[^\s]*r[^\s]*f|-[^\s]*f[^\s]*r|--recursive\s+--force|--force\s+--recursive)", re.I)
DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.I)
TRUNCATE = re.compile(r"\btruncate\b", re.I)
FORCE_PUSH = re.compile(r"\bgit\s+push\b.*(--force|--force-with-lease|-f\b)", re.I)
DELETE_NO_WHERE = re.compile(r"\bdelete\s+from\s+\S+(\s+;)?\s*$", re.I)


def command_from(event: dict) -> str:
    tool_input = event.get("tool_input") or {}
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or tool_input.get("cmd") or "")
    return ""


def reason(cmd: str) -> str | None:
    if RM_RF.search(cmd):
        return "Blocked `rm -rf` (and equivalent flags). Delete specific paths without recursive force."
    if DROP_TABLE.search(cmd):
        return "Blocked `DROP TABLE`. Schema changes belong in a reviewed migration."
    if TRUNCATE.search(cmd):
        return "Blocked `TRUNCATE`."
    if FORCE_PUSH.search(cmd):
        return "Blocked `git push --force` / `-f`. Use a non-force push or ask the human."
    if DELETE_NO_WHERE.search(cmd.strip()):
        return "Blocked `DELETE FROM` without a WHERE clause."
    return None


def deny(msg: str) -> int:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        }
    }
    sys.stdout.write(json.dumps(payload))
    sys.stderr.write(msg + "\n")
    return 0


def log_block(cmd: str, why: str, project: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = "\t".join(
        [
            datetime.now(timezone.utc).isoformat(),
            project.replace("\t", " "),
            why.replace("\t", " "),
            cmd.replace("\n", " ").replace("\t", " "),
        ]
    )
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return 0
    cmd = command_from(event)
    if not cmd:
        return 0
    why = reason(cmd)
    if not why:
        return 0
    project = event.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_block(cmd, why, str(project))
    return deny(why)


if __name__ == "__main__":
    raise SystemExit(main())
