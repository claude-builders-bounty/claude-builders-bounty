#!/usr/bin/env python3
"""
PreToolUse Hook for Claude Code - Destructive Command Guard
Intercepts and blocks dangerous bash/shell and SQL commands before execution.
Author: Rushikesh Garad (github.com/rushikeshgarad2024-dev)
"""
import sys
import re
import json

BLOCKED_PATTERNS = [
    # Filesystem destruction
    r'\brm\s+-[rRfF]+\s+(/|\*|~|\.\.)',
    r'\bmkfs\b',
    r'\bdd\s+if=',
    r'>\s*/dev/sd[a-z]',
    r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', # Fork bomb

    # Git destruction
    r'\bgit\s+push\s+.*--force\b',
    r'\bgit\s+reset\s+--hard\s+HEAD~',

    # SQL destruction without where
    r'\bDROP\s+(DATABASE|TABLE|SCHEMA)\b',
    r'\bTRUNCATE\s+TABLE\b',
    r'\bDELETE\s+FROM\s+\w+\s*(;|$)(?!.*\bWHERE\b)'
]

def check_command(command_str):
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, command_str, re.IGNORECASE):
            return False, pattern
    return True, None

def main():
    # Reads payload from stdin or argument
    input_text = sys.stdin.read().strip() if not sys.stdin.isatty() else (" ".join(sys.argv[1:]) if len(sys.argv) > 1 else "")
    if not input_text:
        sys.exit(0)

    # Try JSON parsing
    cmd = input_text
    try:
        data = json.loads(input_text)
        if isinstance(data, dict):
            cmd = data.get("command", data.get("input", input_text))
    except Exception:
        pass

    is_safe, matched_pattern = check_command(str(cmd))
    if not is_safe:
        print(f"[SECURITY ALERT] Destructive command blocked by Claude Command Guard!", file=sys.stderr)
        print(f"[REASON] Matched dangerous pattern: {matched_pattern}", file=sys.stderr)
        print(f"[BLOCKED COMMAND]: {cmd}", file=sys.stderr)
        sys.exit(2) # Exit code 2 blocks execution

    sys.exit(0)

if __name__ == "__main__":
    main()
