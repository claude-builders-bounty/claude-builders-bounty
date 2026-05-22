#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

def main():
    try:
        # Claude Code pipes tool-use details to the hook via stdin
        input_data = json.load(sys.stdin)
    except Exception:
        # If no valid JSON, let it pass
        sys.exit(0)

    # For Claude Code hooks, the payload typically looks like:
    # { "toolName": "Bash", "args": { "command": "..." } }
    tool_name = input_data.get("toolName", "")
    args = input_data.get("args", {})
    
    # We only care about bash/terminal executions
    if tool_name not in ["Bash", "run_command", "terminal", "execute"]:
        sys.exit(0)

    # Extract command
    command = args.get("command") or args.get("CommandLine") or ""
    if not command:
        sys.exit(0)
        
    blocked = False
    reason = ""

    # Check for destructive patterns
    
    # 1. rm -rf
    if re.search(r'\brm\s+-(?:r|f|rf|fr|R|Rf|rF)\b', command):
        blocked = True
        reason = "Command contains 'rm -rf' (recursive forceful removal)."
        
    # 2. DROP TABLE
    elif re.search(r'\bDROP\s+TABLE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'DROP TABLE'."
        
    # 3. git push --force
    elif re.search(r'\bgit\s+push\s+(?:.*--force|.*-f\b)', command):
        blocked = True
        reason = "Command contains 'git push --force'."
        
    # 4. TRUNCATE
    elif re.search(r'\bTRUNCATE\s+TABLE\b', command, re.IGNORECASE) or re.search(r'\bTRUNCATE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'TRUNCATE'."
        
    # 5. DELETE FROM without WHERE
    elif re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE) and not re.search(r'\bWHERE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'DELETE FROM' without a 'WHERE' clause."
        
    if blocked:
        # Log to ~/.claude/hooks/blocked.log
        hooks_dir = os.path.expanduser("~/.claude/hooks")
        log_file = os.path.join(hooks_dir, "blocked.log")
        timestamp = datetime.datetime.now().isoformat()
        cwd = os.getcwd()
        
        try:
            os.makedirs(hooks_dir, exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] Blocked command: {command} | Project path: {cwd}\n")
        except Exception as e:
            pass # Failsafe
            
        # Display clear message to Claude by printing to stderr and exiting with non-zero
        print(f"ERROR: Claude, your command was BLOCKED by the pre-tool-use hook!\nReason: {reason}\nThis is a safety measure to prevent destructive operations.", file=sys.stderr)
        sys.exit(1)

    # Allow command if safe
    sys.exit(0)

if __name__ == "__main__":
    main()
