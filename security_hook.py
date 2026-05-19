import os
import sys
import re
import datetime

# Configuration
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"DROP\s+TABLE",
    r"git\s+push\s+--force",
    r"TRUNCATE\s+",
    r"DELETE\s+FROM\s+(?!.*\s+WHERE\s+)" # DELETE without WHERE
]

def log_blocked_attempt(command, path):
    """Logs the blocked command details."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] PATH: {path} | COMMAND: {command}\n")

def check_security(command):
    """Checks if the command matches any dangerous patterns."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern
    return False, None

def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    # Claude Code passes the command as a single argument or multiple
    command = " ".join(sys.argv[1:])
    current_path = os.getcwd()

    is_dangerous, pattern = check_security(command)

    if is_dangerous:
        log_blocked_attempt(command, current_path)
        print(f"\n[SECURITY BLOCK] The command contains a dangerous pattern: '{pattern}'")
        print("Reason: This command is flagged as destructive and cannot be executed automatically.")
        print(f"Details logged to: {LOG_FILE}")
        sys.exit(1) # Block execution

    sys.exit(0) # Safe to execute

if __name__ == "__main__":
    main()
