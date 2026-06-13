#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks dangerous bash commands.

Install:
  mkdir -p ~/.claude/hooks/
  cp -r hooks/pre-tool-use-blocker ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre-tool-use-blocker/scripts/blocker.py

Then Claude Code invokes it automatically before every Bash tool call.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    # rm -rf patterns
    (r'\brm\s+.*-[rRfF]+', "Use 'rm' without '-rf' flags, or move to trash instead"),
    (r'\brm\s+.*--recursive\b', "Use 'rmdir' for empty directories or trash for non-empty"),
    
    # git push --force patterns (but allow --force-with-lease)
    (r'\bgit\s+push\s+.*--force\b(?!-with-lease)', 
     "Use 'git push --force-with-lease' instead — it refuses if your local ref is stale"),
    (r'\bgit\s+push\s+.*-f\b(?!orce-with-lease)',
     "The '-f' flag does a hard force-push. Use '--force-with-lease' instead"),
    
    # Destructive SQL patterns
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION|TRIGGER)\b',
     "Destructive SQL — DROP cannot be undone. Use a migration file instead"),
    (r'\bTRUNCATE\b',
     "TRUNCATE wipes all rows instantly. Use DELETE with a WHERE clause, or a migration"),
    
    # DELETE FROM without WHERE (must be checked separately — see below)
]


def has_dangerous_delete(command):
    """Check for DELETE FROM without a WHERE clause."""
    delete_match = re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE)
    if not delete_match:
        return False
    # Check if WHERE appears after the DELETE FROM
    rest = command[delete_match.end():]
    if re.search(r'\bWHERE\b', rest, re.IGNORECASE):
        return False
    return True


def log_blocked(tool_name, command, reason):
    """Append a blocked attempt to the log file."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "command": command[:500],
        "reason": reason,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(tool_name, command):
    """Return (allow: bool, reason: str|None)."""
    if not command:
        return True, None
    
    # Check DELETE FROM without WHERE first
    if has_dangerous_delete(command):
        reason = "DELETE without WHERE clause — this will remove all rows. Add a WHERE condition"
        log_blocked(tool_name, command, reason)
        return False, reason
    
    # Check regex patterns
    for pattern, message in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(tool_name, command, message)
            return False, message
    
    return True, None


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"allow": True}))
            return
        
        payload = json.loads(raw)
        
        tool_name = payload.get("tool_name", payload.get("name", ""))
        args = payload.get("args", payload.get("input", payload.get("arguments", {})))
        command = ""
        
        if isinstance(args, dict):
            command = args.get("command", args.get("cmd", args.get("input", "")))
        elif isinstance(args, str):
            command = args
        else:
            command = str(args)
        
        allow, reason = check_command(tool_name, command)
        
        if allow:
            print(json.dumps({"allow": True}))
        else:
            result = {"allow": False, "message": f"🛑 Blocked by pre-tool-use blocker: {reason}"}
            print(json.dumps(result))
            
    except json.JSONDecodeError:
        print(json.dumps({"allow": True}))
    except Exception as e:
        # Fail open — on errors, allow the command through
        print(json.dumps({"allow": True, "_debug_error": str(e)}))


if __name__ == "__main__":
    main()
