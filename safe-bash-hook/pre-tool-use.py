#!/usr/bin/env python3
import sys
import json
import re
import os
import datetime
import shlex

def install():
    settings_path = os.path.expanduser("~/.claude/settings.json")
    try:
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as f:
                data = json.load(f)
        else:
            data = {"hooks": {"PreToolUse": []}}
    except Exception:
        data = {"hooks": {"PreToolUse": []}}

    if "hooks" not in data:
        data["hooks"] = {}
    if "PreToolUse" not in data["hooks"]:
        data["hooks"]["PreToolUse"] = []
    
    hook_cmd = os.path.abspath(__file__)
    
    hook_exists = False
    for hook_config in data["hooks"]["PreToolUse"]:
        if "hooks" in hook_config:
            for h in hook_config["hooks"]:
                if h.get("command") == hook_cmd:
                    hook_exists = True
                    break
    
    if not hook_exists:
        data["hooks"]["PreToolUse"].append({
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd
                }
            ]
        })
        os.makedirs(os.path.dirname(settings_path), exist_ok=True)
        with open(settings_path, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"✅ Hook successfully registered in {settings_path}")
    else:
        print(f"✅ Hook is already registered in {settings_path}")
    sys.exit(0)

def check_rm_rf(command):
    try:
        parts = shlex.split(command)
    except Exception:
        parts = command.split()
    
    for i, part in enumerate(parts):
        if part == "rm":
            has_r = False
            has_f = False
            for p in parts[i+1:]:
                # If we hit something that doesn't start with '-', it's likely a path or option we shouldn't guess
                if not p.startswith('-'):
                    break
                if p.startswith('--'):
                    if p == '--recursive': has_r = True
                    elif p == '--force': has_f = True
                else:
                    if 'r' in p or 'R' in p: has_r = True
                    if 'f' in p: has_f = True
            if has_r and has_f:
                return True
    
    # Regex fallback for complex strings
    if re.search(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b', command) or \
       re.search(r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b', command) or \
       re.search(r'\brm\s+-[a-zA-Z]*r\b\s+-[a-zA-Z]*f\b', command) or \
       re.search(r'\brm\s+-[a-zA-Z]*f\b\s+-[a-zA-Z]*r\b', command):
        return True
        
    return False

def check_git_push_force(command):
    if "git " in command and "push " in command:
        if "--force" in command or " -f " in command or command.endswith(" -f"):
            return True
    return False

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install()

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        # Not run via Claude Code stdin, do nothing
        sys.exit(0)

    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        cmd_upper = command.upper()
        
        blocked_reason = None
        
        if check_rm_rf(command):
            blocked_reason = "rm -rf (destructive deletion)"
        elif re.search(r'\bDROP\s+TABLE\b', cmd_upper):
            blocked_reason = "DROP TABLE (database schema destruction)"
        elif re.search(r'\bTRUNCATE\s+TABLE\b', cmd_upper) or re.search(r'\bTRUNCATE\b', cmd_upper):
            blocked_reason = "TRUNCATE (database wipe)"
        elif check_git_push_force(command):
            blocked_reason = "git push --force (history rewrite)"
        elif re.search(r'\bDELETE\s+FROM\b', cmd_upper) and not re.search(r'\bWHERE\b', cmd_upper):
            blocked_reason = "DELETE FROM without WHERE clause (mass database deletion)"
            
        if blocked_reason:
            log_dir = os.path.expanduser("~/.claude/hooks")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "blocked.log")
            
            timestamp = datetime.datetime.now().isoformat()
            project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
            clean_cmd = command.replace('\n', ' ').replace('\r', '')
            
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] BLOCKED: {clean_cmd} | PROJECT: {project_path} | REASON: {blocked_reason}\n")
            
            print(f"🛑 BLOCKED: The command was blocked by the safety hook.\nReason: {blocked_reason}.\nDestructive bash commands are not allowed.", file=sys.stderr)
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()