#!/usr/bin/env python3
import sys
import json
import re
import datetime
import os

def log_blocked(command, project_path):
    log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        timestamp = datetime.datetime.now().isoformat()
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] Project: {project_path} | Blocked: {command}\n")
    except Exception:
        pass

def is_destructive(command):
    cmd_lower = command.lower()
    
    # Check rm -rf
    if re.search(r'\brm\s+-r[fv]*\b', cmd_lower):
        args = re.findall(r'\brm\s+-r[fv]*\s+(.*)', cmd_lower)
        if args:
            for arg in args[0].split():
                if arg in ['/', '/*', '*', '.', '.*', '~', '~/*']:
                    return "Blocked destructive command: rm -rf on root/wildcard"

    if "drop table" in cmd_lower:
        return "Blocked destructive SQL command: DROP TABLE"
        
    if re.search(r'\bgit\s+push\s+(.*\s+)?(--force|-f)(\s|$)', cmd_lower):
        return "Blocked destructive command: git push --force"
        
    if "truncate table" in cmd_lower or ("truncate " in cmd_lower and "table " in cmd_lower):
        return "Blocked destructive SQL command: TRUNCATE"
        
    # Check for DELETE FROM without WHERE (handles multiple statements)
    statements = cmd_lower.split(';')
    for stmt in statements:
        if "delete from" in stmt and "where" not in stmt:
            return "Blocked destructive SQL command: DELETE FROM without WHERE clause"
            
    return None

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return
            
        payload = json.loads(input_data)
    except Exception:
        print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
        return

    tool_name = payload.get("toolName", "").lower()
    tool_input = payload.get("toolInput", {})
    project_path = payload.get("projectPath", "unknown")
    
    command = ""
    if tool_name in ["bash", "run_command", "execute"]:
        command = tool_input.get("command", "")
    
    if not command:
        print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
        return

    reason = is_destructive(command)
    
    if reason:
        log_blocked(command, project_path)
        print(json.dumps({
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }))
        return

    print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))

if __name__ == "__main__":
    main()
