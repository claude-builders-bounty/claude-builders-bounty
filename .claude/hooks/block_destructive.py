#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF = re.compile(r"(^|[\s;|&])rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|-fr)(\s|$)", re.I)
GIT_FORCE = re.compile(r"git\s+push.*?(^|\s)(--force|-f)(\s|$)", re.I)
DROP_TABLE = re.compile(r"drop\s+table", re.I)
TRUNCATE = re.compile(r"truncate(\s+table)?\s+", re.I)
DELETE_FROM = re.compile(r"delete\s+from\s+\S+", re.I)
DELETE_WHERE = re.compile(r"delete\s+from\s+.+\s+where\s+", re.I)

def load_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_name": "Bash", "tool_input": {"command": raw}}


def extract(data: dict) -> tuple[str, str, str]:
    tool = str(data.get("tool_name") or data.get("tool") or data.get("name") or "")
    tin = data.get("tool_input") or data.get("input") or data.get("arguments") or {}
    if isinstance(tin, dict):
        cmd = str(tin.get("command") or tin.get("cmd") or tin.get("bash") or "")
    else:
        cmd = str(tin or "")
    if not cmd and isinstance(data.get("command"), str):
        cmd = data["command"]
    project = str(
        data.get("cwd")
        or data.get("project_path")
        or data.get("pwd")
        or os.getcwd()
    )
    return tool, cmd, project

def reason_for(command: str) -> str | None:
    norm = " ".join(command.split())
    if RM_RF.search(norm):
        return "Blocked: destructive recursive delete (rm -rf)."
    if GIT_FORCE.search(norm):
        return "Blocked: force-push to remote (git push --force)."
    if DROP_TABLE.search(norm):
        return "Blocked: DROP TABLE would destroy data."
    if TRUNCATE.search(norm):
        return "Blocked: TRUNCATE would wipe table data."
    if DELETE_FROM.search(norm) and not DELETE_WHERE.search(norm):
        return "Blocked: DELETE FROM without a WHERE clause."
    return None


def main() -> int:
    data = load_payload()
    tool, command, project = extract(data)
    tool_l = tool.lower()
    if tool_l and not any(x in tool_l for x in ("bash", "shell")):
        return 0
    if not command.strip():
        return 0
    why = reason_for(command)
    if not why:
        return 0
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{ts} | project={project} | command={command}\n")
    print(f"{why}\nLogged to {LOG_FILE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
