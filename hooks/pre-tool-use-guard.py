#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code — blocks destructive bash commands.

Installation:
  cp hooks/pre-tool-use-guard.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre-tool-use-guard.py
"""

import json, sys, os, re
from datetime import datetime

BLOCKED_PATTERNS = [
    (r"rm\s+(-[rRf]+\s+)*[/~]", "rm -rf on filesystem root/home"),
    (r"rm\s+(-[rRf]+\s+)+", "rm -rf (recursive force remove)"),
    (r"DROP\s+TABLE", "DROP TABLE statement"),
    (r"DROP\s+DATABASE", "DROP DATABASE statement"),
    (r"TRUNCATE\s+(TABLE\s+)?", "TRUNCATE operation"),
    (r"DELETE\s+FROM\s+\w+(?!.*WHERE)", "DELETE FROM without WHERE clause"),
    (r"git\s+push\s+.*--force", "git push --force"),
    (r"git\s+push\s+.*-f", "git push -f (force)"),
    (r":\(\)\s*\{\s*:\|:&\s*\};:", "fork bomb detected"),
    (r"mkfs\.", "filesystem format command"),
    (r"dd\s+if=.*of=/dev/", "dd write to device"),
    (r">\s*/dev/sd[a-z]", "redirect to block device"),
    (r"chmod\s+(-R\s+)?777\s+/", "chmod 777 on root path"),
    (r"chown\s+(-R\s+)?\S+\s+/", "chown on root path"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
os.makedirs(HOOKS_DIR, exist_ok=True)

def log_blocked(command, reason, project_path):
    timestamp = datetime.now().isoformat()
    entry = f"[{timestamp}] PROJECT={project_path} REASON={reason} COMMAND={command}\n"
    with open(LOG_FILE, "a") as f:
        f.write(entry)

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    if tool_name != "bash":
        print(json.dumps({"continue": True}))
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}))
        return

    project_path = input_data.get("cwd", os.getcwd())

    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, reason, project_path)
            response = {
                "continue": False,
                "reason": (
                    f"\\n========================================\\n"
                    f"🛡️  DESTRUCTIVE COMMAND BLOCKED\\n"
                    f"========================================\\n"
                    f"Command: {command}\\n"
                    f"Blocked: {reason}\\n"
                    f"Project: {project_path}\\n"
                    f"\\nThis command matches a destructive pattern and was"
                    f" intercepted by the pre-tool-use security hook.\\n"
                    f"If you are absolutely sure this is intentional,"
                    f" temporarily disable the hook or modify the command"
                    f" to be more specific.\\n"
                    f"\\nLogged to: {LOG_FILE}\\n"
                )
            }
            print(json.dumps(response))
            return

    print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
