#!/usr/bin/env python3
import sys
import json
import datetime
import os

def log_block(command, reason):
    log_file = os.path.expanduser('~/.claude/hooks/blocked.log')
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    timestamp = datetime.datetime.now().isoformat()
    pwd = os.getcwd()
    with open(log_file, 'a') as f:
        f.write(f"[{timestamp}] BLOCKED: '{command}' | REASON: {reason} | PATH: {pwd}\n")

def main():
    if len(sys.argv) < 2:
        sys.exit(0)
    
    tool_name = sys.argv[1]
    
    # Intercept only bash/command execution tools
    if tool_name.lower() not in ["bash", "run_command", "cmd"]:
        sys.exit(0)
        
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
        data = json.loads(input_data)
        # Handle different parameter names Claude might use for shell execution
        command = data.get("command", "") or data.get("command_line", "") or data.get("script", "") or input_data
    except Exception:
        # Fallback if stdin isn't strictly JSON
        command = input_data

    if not command or not isinstance(command, str):
        sys.exit(0)

    command_upper = command.upper()
    blocked_reason = None
    
    if "RM -RF" in command_upper:
        blocked_reason = "Contains 'rm -rf' which is highly destructive."
    elif "DROP TABLE" in command_upper:
        blocked_reason = "Contains 'DROP TABLE'."
    elif "GIT PUSH --FORCE" in command_upper or "GIT PUSH -F " in command_upper or command_upper.endswith("GIT PUSH -F"):
        blocked_reason = "Contains 'git push --force'."
    elif "TRUNCATE " in command_upper:
        blocked_reason = "Contains 'TRUNCATE'."
    elif "DELETE FROM" in command_upper and "WHERE" not in command_upper:
        blocked_reason = "Contains 'DELETE FROM' without a 'WHERE' clause."
        
    if blocked_reason:
        log_block(command, blocked_reason)
        # Message directly shown to Claude
        print(f"❌ Error: Command execution blocked by pre-tool-use security hook.")
        print(f"Reason: {blocked_reason}")
        print(f"Action taken: Logged to ~/.claude/hooks/blocked.log")
        print(f"Instructions: Do not attempt to bypass this. Ask the user to run the command manually if it is strictly necessary.")
        sys.exit(1) # Return non-zero to block execution
        
    sys.exit(0)

if __name__ == "__main__":
    main()
