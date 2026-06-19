#!/usr/bin/env python3
import sys
import re
import os
import datetime
import json

def is_dangerous(text):
    text_lower = text.lower()
    
    # rm -rf
    if re.search(r"rm\s+-rf", text_lower):
        return "rm -rf"
        
    # DROP TABLE
    if re.search(r"drop\s+table", text_lower):
        return "DROP TABLE"
        
    # git push --force
    if re.search(r"git\s+push\s+--force", text_lower):
        return "git push --force"
        
    # TRUNCATE
    if re.search(r"\btruncate\b", text_lower):
        return "TRUNCATE"
        
    # DELETE FROM without WHERE
    if re.search(r"\bdelete\s+from\b", text_lower):
        if not re.search(r"\bwhere\b", text_lower):
            return "DELETE FROM without WHERE"
            
    return None

def main():
    # Claude passes tool inputs via stdin
    try:
        stdin_content = sys.stdin.read()
    except:
        stdin_content = ""

    # Check arguments
    args_content = " ".join(sys.argv[1:])
    
    text_to_check = args_content + " " + stdin_content
    
    reason = is_dangerous(text_to_check)
    
    if reason:
        # Log to ~/.claude/hooks/blocked.log
        log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        timestamp = datetime.datetime.now().isoformat()
        cwd = os.getcwd()
        
        log_entry = f"[{timestamp}] BLOCKED: {reason} | Path: {cwd} | Command/Input: {text_to_check.strip()[:200]}\n"
        
        with open(log_path, "a") as f:
            f.write(log_entry)
            
        print(f"❌ SECURITY HOOK: Tool execution blocked! Reason: {reason}.")
        print(f"This is a destructive command. If you really need to run this, modify the hook or execute manually.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
