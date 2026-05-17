#!/usr/bin/env python3
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# Log file configuration
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bDROP\s+TABLE\b",
    r"\bgit\s+push\s+--force\b",
    r"\bgit\s+push\s+-f\b",
    r"\bTRUNCATE\b",
]

DELETE_WITHOUT_WHERE = re.compile(r"DELETE\s+FROM\s+(?!.*\bWHERE\b).*", re.IGNORECASE)

def log_blocked(command: str):
    """Log the blocked command to the specified file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    # PWD or default if not set
    pwd = Path.cwd()
    
    log_entry = f"[{timestamp}] BLOCKED: {command} | PATH: {pwd}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        # Ignore logging errors so we don't break the hook flow other than blocking
        pass

def check_command(command: str) -> tuple[bool, str]:
    """Check if the command matches any dangerous patterns."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return False, f"Command contains prohibited pattern: {pattern}"
            
    if "DELETE FROM" in command.upper():
        if DELETE_WITHOUT_WHERE.search(command):
            return False, "DELETE FROM without a WHERE clause is prohibited"
            
    return True, ""

def main():
    # Read the JSON payload from Claude Code
    try:
        payload_str = sys.stdin.read()
        if not payload_str:
            sys.exit(0) # Allow by default if nothing is passed
            
        payload = json.loads(payload_str)
    except ValueError:
        # If payload is malformed, block for safety
        print("Blocked: Malformed JSON payload received by hook.")
        sys.exit(1)

    tool_name = payload.get("toolName", "")
    args = payload.get("args", {})
    
    # We only care about terminal/bash execution tools
    if tool_name not in ["Bash", "terminal", "Terminal"]:
        sys.exit(0) # Allow non-bash tools
        
    command = args.get("command", "")
    if not command:
        sys.exit(0)
        
    is_safe, reason = check_command(command)
    
    if not is_safe:
        log_blocked(command)
        # Required format for Claude to get the block message
        print(f"🛑 Execution Blocked 🛑\nReason: {reason}\nFor your safety, destructive commands are blocked by the pre-tool-use hook. Please use a safer alternative.")
        sys.exit(1)
        
    # Standard output format to allow continuing
    sys.exit(0)

if __name__ == "__main__":
    main()