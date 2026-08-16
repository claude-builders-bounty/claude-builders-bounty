import sys
import json
import re
import os
import datetime

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            print(json.dumps({"decision": "allow"}))
            return
            
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print(json.dumps({"decision": "allow", "reason": "Failed to parse input JSON"}))
        return

    tool_call = data.get("toolCall", {})
    if tool_call.get("name") != "run_command":
        print(json.dumps({"decision": "allow"}))
        return

    args = tool_call.get("args", {})
    command = args.get("CommandLine", "")
    
    blocked = False
    reason = ""

    # Check patterns
    # 1. rm -rf
    if re.search(r'\brm\s+(?:-[^\s]*r[^\s]*f[^\s]*|-[^\s]*f[^\s]*r[^\s]*)', command) or re.search(r'\brm\s+-r\s+-f\b', command) or re.search(r'\brm\s+-f\s+-r\b', command):
        blocked = True
        reason = "Command contains 'rm -rf'"
    
    # 2. DROP TABLE
    elif re.search(r'\bDROP\s+TABLE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'DROP TABLE'"
        
    # 3. git push --force
    elif re.search(r'\bgit\s+push\b.*(?:--force\b|-f\b)', command):
        blocked = True
        reason = "Command contains 'git push --force'"
        
    # 4. TRUNCATE
    elif re.search(r'\bTRUNCATE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'TRUNCATE'"
        
    # 5. DELETE FROM without WHERE
    elif re.search(r'\bDELETE\s+FROM\b', command, re.IGNORECASE) and not re.search(r'\bWHERE\b', command, re.IGNORECASE):
        blocked = True
        reason = "Command contains 'DELETE FROM' without a 'WHERE' clause"

    if blocked:
        # Log to ~/.claude/hooks/blocked.log
        log_dir = os.path.expanduser("~/.claude/hooks")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "blocked.log")
        
        timestamp = datetime.datetime.now().isoformat()
        project_path = data.get("workspacePaths", ["unknown"])[0] if data.get("workspacePaths") else "unknown"
        
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] Command: {command} | Project: {project_path} | Reason: {reason}\n")
            
        print(json.dumps({
            "decision": "deny",
            "reason": f"Destructive command blocked: {reason}"
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
