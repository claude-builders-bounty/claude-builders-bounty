#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash / SQL commands.

Reads one JSON event from stdin. On a match, denies the tool call and
appends a line to ~/.claude/hooks/blocked.log.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Ordered (pattern, reason). First match wins.
RULES = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-rf|-fr)\b", re.I),
     "Blocked rm -rf: recursive force-delete is not allowed by the safety hook."),
    (re.compile(r"\bgit\s+push\b.*(--force|-f)\b", re.I),
     "Blocked git push --force: force-push can rewrite shared history."),
    (re.compile(r"\bDROP\s+TABLE\b", re.I),
     "Blocked DROP TABLE: this permanently deletes a database table."),
    (re.compile(r"\bTRUNCATE\b", re.I),
     "Blocked TRUNCATE: this wipes table data without a WHERE filter."),
    (re.compile(r"\bDELETE\s+FROM\s+\S+(?!\s+WHERE\b)", re.I),
     "Blocked DELETE FROM without WHERE: this would delete every row."),
]


def extract_command(event):
    tool = (event.get("tool_name") or "").lower()
    inp = event.get("tool_input") or {}
    if tool and tool not in ("bash", "powershell"):
        return ""
    for key in ("command", "cmd", "script"):
        val = inp.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""


def match_rule(command):
    if not command:
        return None
    for pat, reason in RULES:
        if pat.search(command):
            # DELETE FROM ... WHERE is allowed; the negative lookahead
            # already covers most cases, but catch "DELETE FROM x WHERE" too.
            if "DELETE" in reason.upper() or "without WHERE" in reason:
                if re.search(r"\bDELETE\s+FROM\b.+\bWHERE\b", command, re.I):
                    continue
            return reason
    return None


def log_block(command, project_path):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\t{project_path}\t{command.replace(chr(9), ' ')}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write(line)


def deny(reason):
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()


def main():
    raw = sys.stdin.read() or ""
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    command = extract_command(event)
    reason = match_rule(command)
    if not reason:
        return 0
    project = (
        event.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    try:
        log_block(command, project)
    except OSError:
        pass
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
