#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

RULES = [
    ("rm -rf", re.compile(r"(?1^\s*|[;&|]\s*)rm\s+(?=[^\n]*\s-[^\n]*r)(?=[^\n]*\s-[^\n]*f)|(?1^\s*|[;&|]\s*)rm\s+-rf(?:\s|$)", re.I)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?|-f)(?:\s|$)", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate(?:\s+table)?\s+[A-Za-z_\"`\[]", re.I)),
]
DELETE_RE = re.compile(r"\bdelete\s+from\b", re.I)
WHERE_RE = re.compile(r"\bwhere\b", re.I)

def find_reason(command: str):
    for label, rx in RULES:
        if rx.search(command):
            return label
    # Split roughly on shell statement boundaries; block DELETE FROM if its statement has no WHERE.
    for stmt in re.split(r"[;\n]|&&|||\|", command):
        if DELETE_RE.search(stmt) and not WHERE_RE.search(stmt):
            return "DELETE FROM without WHERE"
    return None

def log_block(command: str, cwd: str, reason: str):
    path = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{stamp}\tproject={cwd}\treason={reason}\tcommand={safe_command}\n")

def main():
    try:
        payload=json.load(sys.stdin)
    except Exception:
        return 0
    if payload.get("tool_name") != "Bash":
        return 0
    command=str((payload.get("tool_input") or {}).get("command") or "")
    reason=find_reason(command)
    if not reason:
        return 0
    cwd=str(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    log_block(command,cwd,reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command ({reason}). Use a scoped, reversible alternative or ask the user for an explicit safer plan."
        }
    }))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
