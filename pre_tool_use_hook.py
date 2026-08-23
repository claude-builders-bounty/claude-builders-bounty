#!/usr/bin/env python3
import sys
import json
import re
import datetime
import os

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
        event = json.loads(input_data)
    except Exception:
        sys.exit(0)

    # Check if this is a PreToolUse event
    if event.get('type') != 'PreToolUse':
        sys.exit(0)

    # Identify the command from toolInput (handling common tool schema patterns)
    tool_input = event.get('toolInput', {})
    command = tool_input.get('command', '') or tool_input.get('CommandLine', '') or tool_input.get('cmd', '')
    
    if not command and isinstance(tool_input, str):
        command = tool_input

    if not command:
        sys.exit(0)

    # Check for destructive patterns
    blocked = False
    
    # 1. rm -rf
    if re.search(r'\brm\s+-[rR]?[fF][rR]?', command) or re.search(r'\brm\s+-f\s+-r', command) or re.search(r'\brm\s+-r\s+-f', command):
        blocked = True
    # 2. DROP TABLE
    elif re.search(r'(?i)\bDROP\s+TABLE\b', command):
        blocked = True
    # 3. TRUNCATE
    elif re.search(r'(?i)\bTRUNCATE\s+TABLE\b', command) or re.search(r'(?i)\bTRUNCATE\b', command):
        blocked = True
    # 4. git push --force
    elif re.search(r'\bgit\s+push\s+.*?--force\b', command) or re.search(r'\bgit\s+push\s+.*?-f\b', command):
        blocked = True
    # 5. DELETE FROM without WHERE
    elif re.search(r'(?is)\bDELETE\s+FROM\b', command) and not re.search(r'(?is)\bWHERE\b', command):
        blocked = True

    if blocked:
        # Ensure log directory exists
        hooks_dir = os.path.expanduser('~/.claude/hooks')
        os.makedirs(hooks_dir, exist_ok=True)
        log_file = os.path.join(hooks_dir, 'blocked.log')
        
        project_path = event.get('context', {}).get('projectPath', os.getcwd())
        timestamp = datetime.datetime.now().isoformat()
        
        with open(log_file, 'a') as f:
            # Remove newlines for a clean log entry
            clean_cmd = command.replace('\n', ' ')
            f.write(f"[{timestamp}] Project: {project_path} | Blocked: {clean_cmd}\n")
        
        # Display clear message to Claude
        print(f"Action Blocked: The bash command you attempted to run contains destructive patterns (e.g., rm -rf, DROP TABLE, git push --force, or DELETE FROM without WHERE) and was blocked by the safety hook.")
        # Exit with code 2 to instruct Claude Code to block the execution
        sys.exit(2)

    # Exit with 0 to allow the execution
    sys.exit(0)

if __name__ == '__main__':
    main()
