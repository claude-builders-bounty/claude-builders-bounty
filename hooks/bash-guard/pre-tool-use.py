#!/usr/bin/env python3
import sys
import os
import re
import datetime

def block_command(command, reason):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.datetime.now().isoformat()
    pwd = os.getcwd()
    
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] PATH={pwd} CMD={command} REASON={reason}\n")
        
    print(f"Error: Command execution blocked by security policy. Reason: {reason}")
    print(f"The attempt has been logged. Do not attempt this command again.")
    sys.exit(1)

def main():
    if len(sys.argv) < 3:
        sys.exit(0)
        
    tool_name = sys.argv[1]
    
    if tool_name not in ["bash", "execute", "run", "shell"]:
        sys.exit(0)
        
    command = " ".join(sys.argv[2:]).lower()

    if "rm -rf" in command:
        block_command(command, "Contains destructive 'rm -rf' command")
        
    if "drop table" in command:
        block_command(command, "Contains destructive 'DROP TABLE' SQL command")
        
    if "truncate" in command:
        block_command(command, "Contains destructive 'TRUNCATE' SQL command")
        
    if "git push --force" in command or "git push -f" in command:
        block_command(command, "Contains dangerous 'git push --force' command")
        
    if "delete from" in command and "where" not in command:
        block_command(command, "Contains 'DELETE FROM' without a WHERE clause")

    sys.exit(0)

if __name__ == "__main__":
    main()
