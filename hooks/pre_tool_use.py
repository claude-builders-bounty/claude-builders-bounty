#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive commands.
Intercepts dangerous bash/SQL commands before execution.
Requires: Python 3.6+
"""
import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
BLOCK_PATTERNS = [
    (r"rm\s+-rf\s+\.",                          "recursive rm on current dir"),
    (r"DROP\s+TABLE",                           "DROP TABLE — data destruction"),
    (r"TRUNCATE\s+TABLE",                       "TRUNCATE TABLE — full table wipe"),
    (r"DELETE\s+FROM\s+\w+\s*;?\s*$",           "DELETE FROM without WHERE — full table wipe"),
    (r"git\s+push\s+--force",                   "git push --force — history rewrite"),
    (r"git\s+push\s+-f",                        "git push -f — history rewrite"),
    (r"DROP\s+DATABASE",                        "DROP DATABASE — database destruction"),
]

def log_blocked(tool_name: str, command: str, reason: str, cwd: str):
    ts = datetime.now(timezone.utc).isoformat()
    entry = f"[{ts}] BLOCKED tool={tool_name} reason={reason}\n  command={command!r}\n  cwd={cwd}\n\n"
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def check_block(command: str, tool_name: str, cwd: str):
    for pattern, reason in BLOCK_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(tool_name, command, reason, cwd)
            return {
                "decision": "block",
                "reason": f"DESTRUCTIVE_COMMAND: {reason}",
                "metadata": {
                    "original_command": command,
                    "suggestion": "Remove the destructive flag or add a safety condition (e.g., --dry-run) before proceeding."
                }
            }
    return None

def main():
    try:
        payload = json.loads(sys.stdin.read())
    except Exception as e:
        print(json.dumps({"decision": "allow", "reason": f"hook-parse-error: {e}"}))
        return

    tool_name = payload.get("tool_name", "unknown")
    tool_input = payload.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else str(tool_input)
    context = payload.get("context", {}) or {}
    cwd = context.get("cwd", os.getcwd())

    if tool_name in ("Bash", "BashTool", "bash", "Shell"):
        result = check_block(command, tool_name, cwd)
        if result:
            print(json.dumps(result))
            return

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
