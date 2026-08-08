#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime

# Define the log file location
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Destructive regex patterns to block
PATTERNS = [
    r"rm\s+-r[fF]",                         # rm -rf
    r"git\s+push\s+--force",                # git push --force
    r"(?i)\bDROP\s+TABLE\b",                # DROP TABLE
    r"(?i)\bTRUNCATE\b",                    # TRUNCATE
    r"(?i)\bDELETE\s+FROM\b(?!\s+.*WHERE)"  # DELETE FROM without WHERE
]

def log_blocked(command):
    """Logs the blocked command to ~/.claude/hooks/blocked.log"""
    # Ensure directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    project_path = os.getcwd()
    
    log_entry = f"[{timestamp}] PATH: {project_path} | BLOCKED CMD: {command}\n"
    
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to log file: {e}", file=sys.stderr)

def main():
    try:
        # Claude Code hooks pass JSON via stdin
        input_data = sys.stdin.read()
        if not input_data:
            sys.exit(0)
            
        data = json.loads(input_data)
        
        # Check if the tool is executing a shell command
        # Claude Code typically uses tools like 'Bash' or 'run_command'
        command = ""
        if "command" in data:
            command = data["command"]
        elif "arguments" in data and "command" in data["arguments"]:
            command = data["arguments"]["command"]
            
        if not command:
            sys.exit(0) # Allow harmless tools to pass
            
        # Check against dangerous patterns
        for pattern in PATTERNS:
            if re.search(pattern, command):
                log_blocked(command)
                
                # Output a clear rejection message back to Claude
                error_msg = json.dumps({
                    "error": f"❌ SECURITY BLOCK: The command matches a known destructive pattern ('{pattern}'). "
                             f"This action has been blocked and logged for safety. "
                             f"Please reformulate your approach."
                })
                print(error_msg)
                sys.exit(1) # Return non-zero to halt execution
                
        # If no patterns match, allow the command
        sys.exit(0)

    except json.JSONDecodeError:
        # If input is not JSON, let it pass
        sys.exit(0)
    except Exception as e:
        print(json.dumps({"error": f"Hook error: {str(e)}"}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
