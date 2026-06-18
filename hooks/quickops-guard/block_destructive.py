#!/usr/bin/env python3
import sys
import os
import datetime

DANGEROUS_PATTERNS = ["rm -rf", "DROP TABLE", "git push --force", "TRUNCATE", "DELETE FROM"]

def main():
    command = " ".join(sys.argv[1:])
    project_path = os.getcwd()
    timestamp = datetime.datetime.now().isoformat()
    
    for pattern in DANGEROUS_PATTERNS:
        if pattern in command:
            log_entry = f"{timestamp} | {command} | {project_path}\n"
            log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a") as f:
                f.write(log_entry)
            print(f"ERROR: Command blocked by QuickOps Guard: '{pattern}' detected.")
            sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
