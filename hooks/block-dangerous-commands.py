#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands.

Install (2 commands):
  mkdir -p ~/.claude/hooks && cp block-dangerous-commands.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/block-dangerous-commands.py

Then register it in ~/.claude/settings.json (see README.md).

How it works: Claude Code pipes the tool call as JSON on stdin. If the
command matches a destructive pattern, this hook exits 2 and prints the
reason on stderr - Claude Code blocks the call and shows that message to
Claude. Every blocked attempt is appended to ~/.claude/hooks/blocked.log
with timestamp, attempted command, and project path.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# (pattern, human reason). DELETE FROM is only blocked without a WHERE.
RULES = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*[rf][a-zA-Z]*\s+).*(\s|/|\*|~)", re.I),
     "recursive/forced delete (rm -rf)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^|&;]*\s--force\b|\bgit\s+push\s+-f\b", re.I),
     "git push --force"),
    (re.compile(r"\bTRUNCATE\b", re.I), "TRUNCATE"),
]

DELETE_RE = re.compile(r"\bDELETE\s+FROM\b", re.I)
WHERE_RE = re.compile(r"\bWHERE\b", re.I)


def reason_for(cmd: str):
    for rx, why in RULES:
        if rx.search(cmd):
            return why
    if DELETE_RE.search(cmd) and not WHERE_RE.search(cmd):
        return "DELETE FROM without a WHERE clause"
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # not our payload: never interfere
    if payload.get("tool_name") != "Bash":
        return 0
    cmd = (payload.get("tool_input") or {}).get("command", "")
    why = reason_for(cmd)
    if why is None:
        return 0
    project = payload.get("cwd") or (payload.get("tool_input") or {}).get("project_path", "")
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts}\t{project}\t{cmd}\n")
    except OSError:
        pass  # logging must never break the hook
    print(f"Blocked: {why}. This command can destroy data irreversibly. "
          f"Ask the user to run it manually if it is truly intended. "
          f"Logged to {LOG}.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
