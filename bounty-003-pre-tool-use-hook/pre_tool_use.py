#!/usr/bin/env python3
"""
pre_tool_use.py — Claude Code pre-tool-use hook that blocks destructive
bash commands before they are executed.

Install (Claude Code JSON hooks format, Linux/macOS):
  1. mkdir -p ~/.claude/hooks/pre_tool_use
  2. Copy this file there and chmod +x.
  3. Advertise it in settings.json:
       { "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [
           { "type": "command", "command": "~/.claude/hooks/pre_tool_use/pre_tool_use.py" }
       ] } ] } }

Exit codes:
  0  -> allow
  2  -> block (Claude Code semantics for denying a tool call)

Logs every blocked attempt to ~/.claude/hooks/blocked.log with timestamp,
attempted command and project path.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
LOG_DIR = os.path.join(HOME, ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Patterns that are always destructive. The matcher runs on the command string
# the model asked to execute; every match BLOCKS the call.
DANGEROUS_PATTERNS = [
    # rm -rf (with or without --force / -f / /* corner cases)
    re.compile(r"\brm\s+([-]r|[-]R|[-]rf|[-]f+r|[-]r[fR])\b", re.IGNORECASE),
    # SQL destructive statements (optionally followed by a keyword)
    re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    re.compile(r"\bTRUNCATE(?:\s+TABLE)?\s", re.IGNORECASE),
    # DELETE FROM without a WHERE clause (best-effort; matches on the fragment)
    re.compile(r"\bDELETE\s+FROM\b(?:(?!WHERE).)*$", re.IGNORECASE | re.DOTALL),
    # git push --force (or -f shorthand for push)
    re.compile(r"\bgit\s+push\s+.*(--force|-f)\b", re.IGNORECASE),
]


def log_block(cmd, reason):
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{ts} | reason={reason} | cwd={os.getcwd()} | cmd={cmd}\n")


def main():
    # Claude Code passes tool input as JSON to the hook's stdin (Bash tool
    # input = {"command": "..."}); fall back to argv for manual testing.
    raw = ""
    if not sys.stdin.isatty():
        raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        data = {}
    cmd = data.get("command") or (sys.argv[1] if len(sys.argv) > 1 else "")

    if not cmd:
        # Nothing to inspect -> allow (does not meaningfully exist).
        return 0

    for pat in DANGEROUS_PATTERNS:
        m = pat.search(cmd)
        if m:
            reason = f"blocked-pattern:{pat.pattern[:40]}"
            log_block(cmd, reason)
            print(json.dumps({
                "decision": "block",
                "reasons": [reason],
                "message": (
                    "BLOCKED: the requested command matches a destructive "
                    "pattern. Refusing to execute it. If this is intentional, "
                    "ask the user to run it manually in their terminal."
                ),
            }))
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())