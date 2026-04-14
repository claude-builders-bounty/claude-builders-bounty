#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands before execution.
Install: cp pre-tool-use-hook.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-hook.py
"""
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

DANGEROUS_PATTERNS = [
    (r"rm\s+-rf\s+/", "rm -rf / (full system wipe)"),
    (r"rm\s+-rf\s+\$", "rm -rf $ (variable expansion wipe)"),
    (r"rm\s+-rf\s+\.", "rm -rf . (current dir wipe)"),
    (r"DROP\s+TABLE", "DROP TABLE (database destruction)"),
    (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE (database destruction)"),
    (r"git\s+push\s+--force", "git push --force (history rewrite)"),
    (r"git\s+push\s+-f", "git push -f (history rewrite)"),
    (r"DELETE\s+FROM\s+\w+\s*WHERE", "DELETE FROM without proper WHERE check", re.IGNORECASE),
]

def log_blocked(command: str, project_path: str):
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BLOCKED_LOG, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] Blocked: {command} | Project: {project_path}\n")

def check_command(command: str, project_path: str) -> tuple[bool, str]:
    """Returns (blocked, reason)"""
    for pattern in DANGEROUS_PATTERNS:
        flags = pattern[2] if len(pattern) > 2 else 0
        if re.search(pattern[0], command, flags):
            return True, pattern[1]
    return False, ""

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    
    try:
        tool_input = json.loads(sys.argv[1])
    except (json.JSONDecodeError, IndexError):
        sys.exit(0)
    
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)
    
    project_path = os.environ.get("CLAUDE_PROJECT_PATH", "unknown")
    blocked, reason = check_command(command, project_path)
    
    if blocked:
        print(f"\n🚫 BLOCKED: {reason}")
        print(f"   Command: {command}")
        print(f"   Project: {project_path}")
        print(f"   This command was blocked by the pre-tool-use security hook.")
        print(f"   Logged to: {BLOCKED_LOG}")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
