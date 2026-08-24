#!/usr/bin/env python3
"""PreToolUse hook for Claude Code: blocks destructive bash commands."""
import sys, json, re, os
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

def log_blocked(command, reason, cwd):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        entry = json.dumps({"timestamp": ts, "command": command, "reason": reason, "cwd": cwd}) + "\n"
        with open(LOG_PATH, "a") as f:
            f.write(entry)
    except Exception:
        pass

def is_destructive(command):
    """Return reason string if destructive, else None."""
    c = command.lower()
    if re.search(r'\brm\s+-[rf]{1,2}\b', c):
        return "Recursive force delete (rm -rf)"
    if re.search(r'\bdrop\s+table\b', c):
        return "SQL table destruction (DROP TABLE)"
    if re.search(r'\bgit\s+push\s+.*(--force|-f)\b', c):
        return "Force push rewriting remote history"
    if re.search(r'\btruncate\b', c):
        return "SQL table truncation (TRUNCATE)"
    # DELETE FROM without WHERE: find the delete, then check remainder for where
    m = re.search(r'\bdelete\s+from\s+\w+', c)
    if m and not re.search(r'\bwhere\b', c[m.end():]):
        return "Unconditional DELETE FROM without WHERE clause"
    return None

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if payload.get("tool_name") != "Bash":
        print(json.dumps({"block": False}))
        sys.exit(0)

    command = payload.get("tool_input", {}).get("command", "")
    reason = is_destructive(command)
    if reason:
        log_blocked(command, reason, os.getcwd())
        print(json.dumps({"block": True, "reason": f"BLOCKED BY SAFETY HOOK: {reason}. Command '{command}' matches destructive policy."}))
    else:
        print(json.dumps({"block": False}))
    sys.exit(0)

if __name__ == "__main__":
    main()