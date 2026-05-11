#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
Logs blocked attempts to ~/.claude/hooks/blocked.log
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\b", "rm -rf (recursive force delete)"),
    (r"DROP\s+TABLE\b", "DROP TABLE (database table deletion)"),
    (r"git\s+push.*--force\b", "git push --force (force push)"),
    (r"\bTRUNCATE\b", "TRUNCATE (table truncation)"),
    (r"DELETE\s+FROM\b(?!/s+WHERE\b)", "DELETE FROM without WHERE clause"),
]

def log_block(tool_name, command, project_path):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: tool={tool_name} cmd='{command}' path={project_path}\n")

def check_dangerous(command):
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return desc
    return None

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"decision": "allow"}))
        return

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only check bash commands
    if tool_name != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Check for dangerous patterns
    danger_desc = check_dangerous(command)
    if danger_desc:
        project_path = tool_input.get("cwd", "unknown")
        log_block(tool_name, command, project_path)
        print(json.dumps({
            "decision": "block",
            "reason": f"Blocked destructive command: {danger_desc}. Use safer alternatives or add explicit safeguards."
        }))
        return

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
