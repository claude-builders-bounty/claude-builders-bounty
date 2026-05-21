import sys
import json
import re
import os
from datetime import datetime

# Patterns to block (Case-insensitive)
BLOCK_PATTERNS = [
    r"rm\s+-r?[fF]?\s+/",                     # rm -rf /
    r"rm\s+-r?[fF]?\s+\.",                    # rm -rf .
    r"rm\s+-r?[fF]?\s+\*",                    # rm -rf *
    r"DROP\s+TABLE\s+",                       # SQL DROP TABLE
    r"git\s+push\s+.*--force",                # git push --force
    r"git\s+push\s+.*-f(\s|$)",               # git push -f
    r"git\s+push\s+.*--delete",               # git push --delete
    r"git\s+reset\s+--hard",                  # git reset --hard
    r"git\s+branch\s+-D",                     # git branch -D (Force delete)
    r"TRUNCATE\s+",                           # SQL TRUNCATE
    r"DELETE\s+FROM\s+(?!.*\s+WHERE\s+)",     # SQL DELETE FROM without WHERE
    r"mkfs\..*",                              # Formatting disks
    r"dd\s+if=.*of=/dev/.*",                  # Direct disk writes
    r"chmod\s+777\s+",                        # Dangerous permissions
    r"shred\s+",                              # Shredding files
    r"history\s+-c",                          # Clear history
]

def log_blocked(command):
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            project_path = os.getcwd()
            f.write(f"[{timestamp}] PROJECT: {project_path} | COMMAND: {command}\n")
    except Exception as e:
        sys.stderr.write(f"Error writing to log: {str(e)}\n")

def main():
    try:
        # Claude Code sends JSON to stdin
        # Format: { "tool_name": "Bash", "tool_input": { "command": "..." }, ... }
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)

        data = json.loads(input_data)
        tool_name = data.get("tool_name")
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")

        if tool_name == "Bash" and command:
            for pattern in BLOCK_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    log_blocked(command)
                    # Return blocking decision to stdout
                    print(json.dumps({
                        "decision": "deny",
                        "reason": f"🛑 SECURITY ALERT: Destructive command detected!\n\nCommand: {command}\nMatched Rule: {pattern}\n\nThis command has been blocked to prevent accidental data loss or security breaches. If you are SURE you want to run this, please execute it manually in your terminal outside of the AI environment."
                    }))
                    # Exit 2 to signal blocking to Claude Code
                    sys.exit(2)

        # If no dangerous patterns found
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Fallback for non-JSON input
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)
    except Exception as e:
        # Safety fallback
        sys.stderr.write(f"Hook error: {str(e)}\n")
        print(json.dumps({"decision": "allow"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
