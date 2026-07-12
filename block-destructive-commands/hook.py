#!/usr/bin/env python3
import sys
import json
import re
import datetime
import os
import shutil

def install():
    hooks_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    
    script_path = os.path.join(hooks_dir, "block_destructive.py")
    shutil.copyfile(sys.argv[0], script_path)
    os.chmod(script_path, 0o755)
    
    settings_file = os.path.expanduser("~/.claude/settings.json")
    settings = {}
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
        except Exception:
            pass
            
    if "hooks" not in settings:
        settings["hooks"] = {}
    if "PreToolUse" not in settings["hooks"]:
        settings["hooks"]["PreToolUse"] = []
        
    # Check if already installed
    installed = False
    for hook_config in settings["hooks"]["PreToolUse"]:
        if hook_config.get("matcher") == "Bash":
            for hook in hook_config.get("hooks", []):
                if hook.get("command") == script_path:
                    installed = True
                    
    if not installed:
        settings["hooks"]["PreToolUse"].append({
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": script_path
                }
            ]
        })
        with open(settings_file, "w") as f:
            json.dump(settings, f, indent=2)
            
    print("✅ Successfully installed hook to ~/.claude/hooks/block_destructive.py")
    print("✅ Updated ~/.claude/settings.json")
    sys.exit(0)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        install()
        
    if sys.stdin.isatty():
        # If run without stdin and not installing, print help
        print("This script is a Claude Code PreToolUse hook.")
        print("Run with --install to install the hook.")
        sys.exit(0)
        
    input_data = sys.stdin.read()
    if not input_data:
        sys.exit(0)
        
    try:
        context = json.loads(input_data)
    except json.JSONDecodeError:
        # If it's not JSON, let it proceed normally
        sys.exit(0)
        
    command = ""
    if isinstance(context, dict):
        if "command" in context:
            command = context["command"]
        elif "parameters" in context and isinstance(context["parameters"], dict) and "command" in context["parameters"]:
            command = context["parameters"]["command"]
            
    # Fallback to stringifying the whole context
    if not command:
        command = json.dumps(context)
        
    patterns = [
        (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f', 'rm -rf'),
        (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r', 'rm -rf'),
        (r'\brm\s+-[a-zA-Z]*r\b\s+-[a-zA-Z]*f\b', 'rm -rf'),
        (r'\brm\s+-[a-zA-Z]*f\b\s+-[a-zA-Z]*r\b', 'rm -rf'),
        (r'(?i)\bDROP\s+TABLE\b', 'DROP TABLE'),
        (r'\bgit\s+push\s+--force\b', 'git push --force'),
        (r'\bgit\s+push\s+-f\b', 'git push --force'),
        (r'(?i)\bTRUNCATE\b', 'TRUNCATE')
    ]
    
    blocked_reason = None
    
    for pattern, name in patterns:
        if re.search(pattern, command):
            blocked_reason = name
            break
            
    if not blocked_reason:
        # Check for DELETE FROM without WHERE
        delete_matches = re.finditer(r'(?i)\bDELETE\s+FROM\b', command)
        for match in delete_matches:
            after_delete = command[match.end():]
            if not re.search(r'(?i)\bWHERE\b', after_delete):
                blocked_reason = 'DELETE FROM without WHERE clause'
                break

    if blocked_reason:
        log_file = os.path.expanduser("~/.claude/hooks/blocked.log")
        timestamp = datetime.datetime.now().isoformat()
        project_path = os.environ.get('PWD', 'Unknown')
        
        try:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"[{timestamp}] Blocked: {blocked_reason} | Command: {repr(command)} | Path: {project_path}\n")
        except Exception:
            pass # Continue to block even if logging fails
            
        print(f"ERROR: Destructive command blocked by Claude Code PreToolUse hook.")
        print(f"Reason: Found blocked pattern '{blocked_reason}'.")
        sys.exit(1)
        
    sys.exit(0)

if __name__ == "__main__":
    main()
