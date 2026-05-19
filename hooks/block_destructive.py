import sys
import json
import re
import os
from datetime import datetime

# Path to the log file as per bounty requirements
LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Dangerous patterns and their corresponding reasons
DANGEROUS_PATTERNS = [
    (r"rm\s+(-rf|-fr|--recursive\s+--force)", "Deletion of files/directories with 'rm -rf' is restricted."),
    (r"DROP\s+TABLE", "SQL 'DROP TABLE' commands are restricted."),
    (r"git\s+push\s+.*(-f\b|--force\b)", "Force pushing to git repositories is restricted."),
    (r"TRUNCATE\b", "SQL 'TRUNCATE' commands are restricted."),
    (r"DELETE\s+FROM\s+(?!.*\bWHERE\b)", "SQL 'DELETE FROM' without a 'WHERE' clause is restricted.")
]

def log_blocked(command, cwd):
    """Logs the blocked command details to the log file."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        timestamp = datetime.now().isoformat()
        with open(LOG_PATH, "a") as f:
            f.write(f"{timestamp}, {command}, {cwd}\n")
    except Exception as e:
        # Fallback to stderr if logging fails
        sys.stderr.write(f"Failed to log blocked command: {e}\n")

def main():
    # Pre-tool-use hooks receive JSON via stdin
    try:
        input_data = json.load(sys.stdin)
    except Exception:
        # Default to allow if input is malformed to avoid blocking Claude unnecessarily
        print(json.dumps({"permissionDecision": "allow"}))
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    cwd = input_data.get("context", {}).get("cwd", os.getcwd())

    # Check if the tool is bash-related
    if tool_name in ["Bash", "run_shell_command"] and command:
        for pattern, reason in DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                log_blocked(command, cwd)
                # Return the deny decision in JSON format
                print(json.dumps({
                    "permissionDecision": "deny",
                    "reason": f"SECURITY BLOCK: {reason} This attempt has been logged."
                }))
                return

    # Allow the command if no dangerous patterns match
    print(json.dumps({"permissionDecision": "allow"}))

if __name__ == "__main__":
    main()
