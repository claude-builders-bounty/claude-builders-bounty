#!/usr/bin/env python3
import sys
import json
import re
from datetime import datetime
from pathlib import Path

def main():
    # Parse input provided by Claude Code hook interface
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # Allow if input parsing fails unexpectedly

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # We only need to check bash execution tools
    if tool_name not in ["Bash", "bash"]:
        sys.exit(0)

    command = tool_input.get("command", "")
    project_path = input_data.get("cwd", input_data.get("project_path", "Unknown"))

    # Block patterns required by criteria
    blocked_patterns = [
        (r"\brm\s+-rf\b", "rm -rf command detected"),
        (r"\bDROP\s+TABLE\b", "DROP TABLE statement detected"),
        (r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+-f\b", "git push --force detected"),
        (r"\bTRUNCATE\b", "TRUNCATE statement detected"),
        (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without a WHERE clause detected")
    ]

    for pattern, reason in blocked_patterns:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            # 1. Log blocked attempt to ~/.claude/hooks/blocked.log
            log_dir = Path.home() / ".claude" / "hooks"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "blocked.log"
            
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] PROJECT: {project_path} | COMMAND: {command} | REASON: {reason}\n"
            
            with open(log_file, "a") as f:
                f.write(log_entry)

            # 2. Display clear error message to Claude and exit with non-zero status
            print(f"BLOCKED BY SECURITY HOOK: {reason}. Command: '{command}' was prevented from executing.", file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()