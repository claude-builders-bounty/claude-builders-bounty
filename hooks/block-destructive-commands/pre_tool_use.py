#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime

# Destructive patterns
PATTERNS = [
    # rm -rf, rm -fr, rm -r -f, rm -f -r
    (re.compile(r'\brm\b.*\B-(r\s*-f|f\s*-r|rf|fr)\b'), "rm -rf"),
    # DROP TABLE
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE"),
    # git push --force or git push -f
    (re.compile(r'\bgit\s+push\b.*\B(--force|-f)\b'), "git push --force"),
    # TRUNCATE
    (re.compile(r'\bTRUNCATE\b(\s+TABLE)?\b', re.IGNORECASE), "TRUNCATE"),
]

# DELETE FROM without WHERE
DELETE_FROM_RE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
WHERE_RE = re.compile(r'\bWHERE\b', re.IGNORECASE)

def is_destructive(command):
    command_str = str(command)
    
    # Check simple patterns
    for pattern, name in PATTERNS:
        if pattern.search(command_str):
            return True, f"Blocked by rule: {name}"
            
    # Check DELETE FROM without WHERE
    if DELETE_FROM_RE.search(command_str):
        if not WHERE_RE.search(command_str):
            return True, "Blocked by rule: DELETE FROM without WHERE clause"
            
    return False, ""

def log_blocked(command, rule, cwd):
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "blocked.log")
    
    timestamp = datetime.datetime.now().isoformat()
    try:
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] CWD: {cwd} | RULE: {rule} | CMD: {command}\n")
    except Exception:
        pass # Best effort logging

def main():
    try:
        # Claude Code passes JSON via stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
            
        payload = json.loads(input_data)
        
        # Check if it's a bash command. Claude Code tool is typically 'Bash' or 'run_command'
        # The command string is typically in payload['input']['command']
        tool_name = payload.get("toolName", "")
        tool_input = payload.get("input", {})
        
        command = ""
        if "command" in tool_input:
            command = tool_input["command"]
        elif "CommandLine" in tool_input: # For other agent formats
            command = tool_input["CommandLine"]
            
        if not command:
            sys.exit(0)
            
        blocked, reason = is_destructive(command)
        
        if blocked:
            cwd = os.getcwd()
            log_blocked(command, reason, cwd)
            # Claude Code hooks format: stderr is printed to Claude, exit 1 blocks the tool
            sys.stderr.write(f"\n[SECURITY HOOK] Command execution blocked!\nReason: {reason}\n")
            sys.stderr.write("This action is considered destructive and is blocked by the pre-tool-use hook.\n")
            sys.exit(1)
            
    except Exception as e:
        # Fail open if payload parsing fails or something goes wrong
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
