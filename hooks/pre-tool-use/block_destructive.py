#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Install: ln -sf $(pwd)/block_destructive.py ~/.claude/hooks/pre-tool-use/block_destructive.py
"""

import json, os, sys, re, time
from pathlib import Path

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Dangerous patterns (case-insensitive)
DANGEROUS_PATTERNS = [
    # File destruction
    (r'\brm\s+-rf\b', 'Recursive force delete — use targeted rm instead'),
    (r'\brm\s+-rf\s+/\b', 'Attempted to delete root filesystem — BLOCKED'),
    (r'\brm\s+-rf\s+/\*', 'Attempted to delete all files — BLOCKED'),
    (r'\brm\s+-rf\s+\*', 'Bulk delete in current directory — use targeted deletes'),
    (r'\bmv\s+[^\s]+\s+/dev/null\b', 'Moving file to /dev/null = data destruction'),
    
    # Git destructive
    (r'\bgit\s+push\s+--force\b', 'Force push rewrites history — use --force-with-lease'),
    (r'\bgit\s+push\s+-f\b', 'Force push rewrites history — use --force-with-lease'),
    (r'\bgit\s+reset\s+--hard\b', 'Hard reset discards changes — verify first'),
    (r'\bgit\s+clean\s+-fd\b', 'Force clean deletes untracked files'),
    
    # Database destructive
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'Destructive DDL — BLOCKED'),
    (r'\bTRUNCATE\b', 'Table truncation — use DELETE with WHERE'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE without WHERE clause — BLOCKED'),
    (r'\bUPDATE\s+\w+\s+SET\b(?!.*\bWHERE\b)', 'UPDATE without WHERE clause — BLOCKED'),
    
    # System dangerous
    (r'\bchmod\s+-R\s+777\b', 'Overly permissive recursive chmod'),
    (r'\bchown\s+-R\b', 'Recursive ownership change'),
    (r'\bdd\s+if=[^\s]+\s+of=[^\s]', 'dd disk operation — verify device target'),
    (r'\bmkfs\.', 'Filesystem creation — destructive'),
    (r'\bfdisk\b', 'Partition table modification'),
    (r'\b>:?\s*[a-zA-Z0-9_]+\s*$', 'Redirect truncation overwrites file'),
]

def check_command(cmd: str) -> tuple:
    """Check if a command is dangerous. Returns (blocked: bool, reason: str)"""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return True, reason
    return False, ""

def log_block(cmd: str, reason: str, cwd: str = ""):
    """Log a blocked command attempt"""
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "command": cmd[:200],
        "reason": reason,
        "project": cwd or os.getcwd(),
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    # Read tool call from stdin (Claude Code hook format)
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input means we don't block
            sys.exit(0)
        
        payload = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # If we can't parse, allow through
        sys.exit(0)
    
    # Extract the command from various possible payload shapes
    cmd = ""
    if isinstance(payload, dict):
        # Tool use format
        tool_name = payload.get("tool_name", "") or payload.get("name", "")
        if "bash" in tool_name.lower() or "tool" in tool_name.lower():
            cmd = payload.get("arguments", {}).get("command", "") or payload.get("input", "")
        elif "command" in payload.get("arguments", {}):
            cmd = payload["arguments"]["command"]
        elif "input" in payload:
            cmd = payload.get("input", "")
    
    if not cmd:
        sys.exit(0)
    
    blocked, reason = check_command(cmd)
    if blocked:
        log_block(cmd, reason)
        error_msg = {
            "is_error": True,
            "type": "blocked",
            "content": f"⛔ BLOCKED: {reason}\n\nUse a safer alternative. See ~/.claude/hooks/blocked.log for the full record."
        }
        print(json.dumps(error_msg))
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
