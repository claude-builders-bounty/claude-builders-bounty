#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code to block destructive bash and SQL commands.
Exit code 2 blocks execution; exit code 0 allows execution.
"""
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Specifically check DELETE FROM to only block when WHERE is absent
DELETE_WITHOUT_WHERE_REGEX = re.compile(r"\bDELETE\s+FROM\s+\w+\s*(?!.*\bWHERE\b)", re.IGNORECASE)

def extract_command(raw_input: str) -> str:
    """Extract command string from stdin payload or raw string."""
    raw_input = raw_input.strip()
    if not raw_input:
        return ""
    try:
        data = json.loads(raw_input)
        if isinstance(data, dict):
            # Check Claude Code tool_input format: {"tool_input": {"command": "..."}}
            cmd = data.get("tool_input", {}).get("command")
            if isinstance(cmd, str):
                return cmd
            for key in ("command", "cmd", "input", "shell", "script"):
                val = data.get(key)
                if isinstance(val, str):
                    return val
    except json.JSONDecodeError:
        pass
    return raw_input

def is_destructive(cmd: str) -> Tuple[bool, str]:
    """Check if command contains destructive bash or SQL patterns."""
    if not cmd:
        return False, ""
    
    # Check DELETE FROM without WHERE
    if DELETE_WITHOUT_WHERE_REGEX.search(cmd):
        return True, "DELETE FROM without a WHERE clause"
    
    # Check other patterns
    if re.search(r"\bgit\s+push\s+.*(?:--force|-f)\b", cmd, re.IGNORECASE):
        return True, "git push --force (-f)"
    if re.search(r"\bDROP\s+TABLE\b", cmd, re.IGNORECASE):
        return True, "DROP TABLE"
    if re.search(r"\bTRUNCATE\b", cmd, re.IGNORECASE):
        return True, "TRUNCATE"
    if re.search(r"\brm\s+-[a-zA-Z]*[rfRF][a-zA-Z]*[rfRF][a-zA-Z]*\b|\brm\s+-(?:[rR][fF]|[fF][rR])\b", cmd):
        return True, "rm -rf"
    
    return False, ""

def log_blocked_attempt(cmd: str, reason: str, log_file: Optional[Path] = None) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log with ISO timestamp."""
    if log_file is None:
        log_file = Path.home() / ".claude" / "hooks" / "blocked.log"
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] BLOCKED ({reason}): {cmd}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Failed to write to blocked.log: {e}\n")

def main() -> int:
    raw_input = sys.stdin.read()
    cmd = extract_command(raw_input)
    blocked, reason = is_destructive(cmd)
    
    if blocked:
        log_blocked_attempt(cmd, reason)
        sys.stderr.write(f"🛑 PreToolUse Hook Blocked Destructive Command ({reason}):\n{cmd}\n")
        return 2  # Exit code 2 blocks tool execution per specification
    return 0

if __name__ == "__main__":
    sys.exit(main())