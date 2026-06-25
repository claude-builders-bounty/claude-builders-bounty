#!/usr/bin/env python3
import sys
import json
import re
import os
from datetime import datetime

BLOCKED_LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

def check_rm_rf(command):
    pattern1 = r'\brm\b.*?\s-[a-zA-Z]*(?:[rR][a-zA-Z]*f|f[a-zA-Z]*[rR])[a-zA-Z]*\b'
    pattern2 = r'\brm\b.*?\s(?:-[rR]|--recursive)\b.*?\s(?:-f|--force)\b'
    pattern3 = r'\brm\b.*?\s(?:-f|--force)\b.*?\s(?:-[rR]|--recursive)\b'
    if re.search(pattern1, command) or re.search(pattern2, command) or re.search(pattern3, command):
        return "rm -rf (recursive force deletion)"
    return None

def check_drop_table(command):
    if re.search(r'\bdrop\s+table\b', command, re.IGNORECASE):
        return "DROP TABLE (database table deletion)"
    return None

def check_git_push_force(command):
    if re.search(r'\bgit\s+push\b.*?\s(?:--force|-f\b)', command, re.IGNORECASE):
        return "git push --force (force pushing to repository)"
    return None

def check_truncate(command):
    if re.search(r'\btruncate\b', command, re.IGNORECASE):
        return "TRUNCATE (database table truncation)"
    return None

def check_delete_without_where(command):
    statements = command.split(';')
    for stmt in statements:
        if re.search(r'\bdelete\s+from\b', stmt, re.IGNORECASE):
            if not re.search(r'\bwhere\b', stmt, re.IGNORECASE):
                return "DELETE FROM without a WHERE clause (unrestricted database deletion)"
    return None

def is_safe_command_prefix(command):
    command_clean = command.strip()
    safe_prefixes = ('echo ', 'printf ', 'cat ', 'grep ', 'git diff', 'git show', 'git log', 'git status')
    if any(command_clean.startswith(prefix) for prefix in safe_prefixes):
        if not any(char in command for char in ('|', '>', '<', '$', '`')):
            return True
    return False

def is_destructive(command):
    if is_safe_command_prefix(command):
        return None
        
    violations = []
    rm_rf = check_rm_rf(command)
    if rm_rf: violations.append(rm_rf)
    
    drop_table = check_drop_table(command)
    if drop_table: violations.append(drop_table)
    
    git_push = check_git_push_force(command)
    if git_push: violations.append(git_push)
    
    truncate = check_truncate(command)
    if truncate: violations.append(truncate)
    
    delete_where = check_delete_without_where(command)
    if delete_where: violations.append(delete_where)
    
    return violations if violations else None

def main():
    try:
        # Read JSON from stdin
        input_data = sys.stdin.read()
        if not input_data.strip():
            sys.exit(0)
            
        data = json.loads(input_data)
        
        # Check if the event is PreToolUse and tool is Bash
        event = data.get("hook_event_name")
        tool = data.get("tool_name")
        
        if event != "PreToolUse" or tool != "Bash":
            sys.exit(0)
            
        tool_input = data.get("tool_input", {})
        command = tool_input.get("command", "")
        project_path = data.get("cwd", os.getcwd())
        
        violations = is_destructive(command)
        
        if violations:
            timestamp = datetime.now().isoformat()
            
            # Log the blocked attempt
            os.makedirs(os.path.dirname(BLOCKED_LOG_PATH), exist_ok=True)
            with open(BLOCKED_LOG_PATH, "a") as f:
                f.write(f"[{timestamp}] Path: {project_path} | Command: {command} | Violations: {', '.join(violations)}\n")
                
            # Print error to stderr
            sys.stderr.write(f"\nERROR: Blocked by Destructive Command Guard!\n")
            sys.stderr.write(f"Attempted command: {command}\n")
            sys.stderr.write(f"Violations detected:\n")
            for violation in violations:
                sys.stderr.write(f" - {violation}\n")
            sys.stderr.write(f"This command is blocked for safety. Use a non-destructive alternative.\n\n")
            sys.exit(2)
            
    except Exception as e:
        sys.stderr.write(f"Destructive Command Guard Hook Error: {str(e)}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
