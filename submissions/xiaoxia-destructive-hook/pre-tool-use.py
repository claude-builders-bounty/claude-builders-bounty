#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks destructive bash commands.
Bounty #3: $100 — claude-builders-bounty
"""
import sys, json, os, re
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-rf\b', "Recursive force delete"),
    (r'\bDROP\s+TABLE\b', "Database table destruction (DROP TABLE)", True),
    (r'\bDROP\s+DATABASE\b', "Database destruction (DROP DATABASE)", True),
    (r'\bTRUNCATE\b', "Table truncation — instant, no rollback", True),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "DELETE FROM without WHERE — deletes all rows", True),
    (r'\bgit\s+push\s+.*--force\b', "Force push — overwrites remote history"),
    (r'\bgit\s+reset\s+--hard\b', "Hard reset — discards all uncommitted changes"),
    (r'\bchmod\s+777\b', "World-writable permissions"),
    (r'\bdd\s+if=.*of=/dev/', "Direct device write — can wipe disk"),
    (r':\(\)\s*\{\s*:\|:&\s*\}\s*;?\s*:', "Fork bomb — system crash risk"),
]

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def is_destructive(command: str) -> tuple[bool, str]:
    """Check if a command matches destructive patterns."""
    for pattern, reason, *extras in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def log_block(command: str, reason: str, project: str = ""):
    """Log blocked attempt."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project='{project}' | reason='{reason}' | command='{command[:200]}'\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

try:
    input_data = json.load(sys.stdin)
except (json.JSONDecodeError, Exception):
    # Non-JSON input — allow through
    sys.exit(0)

tool_name = input_data.get("tool_name", "")
if tool_name != "Bash":
    # Not a bash tool call — pass through
    sys.exit(0)

command = input_data.get("tool_input", {}).get("command", "")
if not command:
    sys.exit(0)

destructive, reason = is_destructive(command)
if destructive:
    project = os.getcwd()
    log_block(command, reason, project)
    
    print(json.dumps({
        "decision": "block",
        "reason": f"BLOCKED: {reason}\nCommand: {command[:200]}\n"
                  f"If you intentionally need this, run it manually in a terminal."
    }))
    sys.exit(0)

# Safe command — allow through
sys.exit(0)
