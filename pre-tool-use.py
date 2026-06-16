import sys
import datetime
import os

# Blocked patterns
BLOCKED_PATTERNS = [
    "rm -rf",
    "DROP TABLE",
    "git push --force",
    "TRUNCATE",
    "DELETE FROM" # Simplified check for WHERE clause handled below
]

def main():
    if len(sys.argv) < 2:
        sys.exit(0)

    command = sys.argv[1]
    project_path = os.getcwd()
    
    # Check for DELETE FROM without WHERE
    if "DELETE FROM" in command.upper() and "WHERE" not in command.upper():
        blocked = True
        reason = "DELETE FROM without WHERE clause is blocked"
    else:
        blocked = False
        for pattern in BLOCKED_PATTERNS:
            if pattern in command:
                blocked = True
                reason = f"Command pattern '{pattern}' is blocked"
                break

    if blocked:
        timestamp = datetime.datetime.now().isoformat()
        log_entry = f"[{timestamp}] CMD: {command} | PATH: {project_path}\n"
        
        try:
            with open(os.path.expanduser("~/.claude/hooks/blocked.log"), "a") as log_file:
                log_file.write(log_entry)
        except Exception as e:
            # Silently fail log write but still block
            pass

        print(f"❌ ERROR: The command '{command}' was blocked for security reasons: {reason}")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
