#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

def main():
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # If we can't parse the payload, allow execution
        sys.exit(0)

    # Claude Code passes tool_name and tool_input in the payload
    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    
    # We only care about Bash/command executions
    if "bash" not in tool_name.lower() and "cmd" not in tool_name.lower() and "run" not in tool_name.lower():
        sys.exit(0)

    # Extract command from tool_input
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        sys.exit(0)

    blocked = False
    reason = ""

    # Destructive patterns
    if re.search(r'\brm\s+-r?f\b', command) or re.search(r'\brm\s+-f?r\b', command):
        blocked = True
        reason = "rm -rf is a destructive command."
    elif re.search(r'\bDROP\s+TABLE\b', command, re.IGNORECASE):
        blocked = True
        reason = "DROP TABLE is a destructive database command."
    elif re.search(r'\bgit\s+push\s+--force\b', command) or re.search(r'\bgit\s+push\s+-f\b', command):
        blocked = True
        reason = "git push --force is destructive and can overwrite history."
    elif re.search(r'\bTRUNCATE\b', command, re.IGNORECASE):
        blocked = True
        reason = "TRUNCATE is a destructive database command."
    elif re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE) and not re.search(r'\bWHERE\b', command, re.IGNORECASE):
        blocked = True
        reason = "DELETE FROM without a WHERE clause is destructive."

    if blocked:
        # Log to ~/.claude/hooks/blocked.log
        log_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "blocked.log")
        
        timestamp = datetime.datetime.now().isoformat()
        project_path = os.getcwd()
        
        try:
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] Command: {command} | Project: {project_path}\n")
        except Exception:
            pass # Failsafe
            
        print(f"Command blocked by pre-tool-use hook: {reason}")
        sys.exit(2) # Exit code 2 blocks the tool call in Claude Code

    sys.exit(0)

if __name__ == "__main__":
    main()
