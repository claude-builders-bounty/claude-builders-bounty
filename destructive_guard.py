import sys
import json
import re
import os
import datetime

def strip_quotes(s):
    # Remove all text inside single and double quotes to avoid false positives
    s = re.sub(r"'[^']*'", "''", s)
    s = re.sub(r'"[^"]*"', '""', s)
    return s

def is_dangerous(command):
    # Strip quotes before checking
    command = strip_quotes(command)
    
    # 1. rm -rf
    subcmds = re.split(r'[;&|]', command)
    for subcmd in subcmds:
        if re.search(r'\brm\b', subcmd):
            has_r = bool(re.search(r'(?:\s|^)-(?:[a-zA-Z]*)[rR]', subcmd) or re.search(r'(?:\s|^)--recursive\b', subcmd))
            has_f = bool(re.search(r'(?:\s|^)-(?:[a-zA-Z]*)[fF]', subcmd) or re.search(r'(?:\s|^)--force\b', subcmd))
            if has_r and has_f:
                return "rm -rf"
                
    # 2. DROP TABLE
    if re.search(r'(?i)\bDROP\s+TABLE\b', command):
        return "DROP TABLE"
        
    # 3. git push --force
    for subcmd in subcmds:
        if re.search(r'\bgit\s+push\b', subcmd):
            if re.search(r'(?:\s|^)(?:--force|-f)\b', subcmd):
                return "git push --force"
                
    # 4. TRUNCATE
    if re.search(r'(?i)\bTRUNCATE\b(?:\s+TABLE)?', command):
        return "TRUNCATE"
        
    # 5. DELETE FROM without WHERE
    for subcmd in subcmds:
        if re.search(r'(?i)\bDELETE\s+FROM\b', subcmd):
            if not re.search(r'(?i)\bWHERE\b', subcmd):
                return "DELETE FROM without WHERE"
                
    return None

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return
            
        payload = json.loads(input_data)
        
        # Only check Bash tool
        if payload.get("tool_name") != "Bash":
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)
            
        command = payload.get("tool_input", {}).get("command", "")
        if not command:
            print(json.dumps({"decision": "allow"}))
            sys.exit(0)
            
        reason = is_dangerous(command)
        if reason:
            # Log the attempt
            log_dir = os.path.expanduser("~/.claude/hooks")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "blocked.log")
            
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
            cwd = payload.get("cwd", os.getcwd())
            
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] BLOCKED: {reason} | CWD: {cwd} | CMD: {command}\n")
                
            # Block the command
            print(json.dumps({
                "decision": "deny",
                "reason": f"Command blocked by pre-tool-use hook: contains dangerous pattern '{reason}'"
            }))
            sys.exit(0)
            
        print(json.dumps({"decision": "allow"}))
        
    except Exception as e:
        # Fallback allow to avoid breaking Claude if script fails
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
