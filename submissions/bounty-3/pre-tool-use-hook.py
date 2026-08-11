#!/usr/bin/env python3
"""
Pre-Tool-Use Hook: Blocks Destructive Bash Commands
Bounty #3 - $100 - claude-builders-bounty

Blocks dangerous bash commands before execution.
Logs attempts to ~/.claude/hooks/blocked.log
"""

import os, sys, json, re, datetime

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+(-[a-zA-Z]*r[a-zA-Z]*[f]?|[a-zA-Z]*f[a-zA-Z]*r?)\b', 'rm with recursive/force flags'),
    (r'\brm\s+(-[a-zA-Z]*rf[a-zA-Z]*)\b', 'rm -rf (recursive force delete)'),
    (r'\brm\s+-[a-zA-Z]*\b.*\b/(etc|var|usr|boot|home|root|dev|proc|sys)\b', 'rm targeting critical system directory'),
    (r'\bdd\s+if=.*\bof=/dev/', 'dd writing to raw device'),
    (r'\.'+r'mkfs\b', 'filesystem format command'),
    (r'\b>:?\s*/dev/sd[a-z]', 'redirect to raw block device'),
    (r'\bchmod\s+(-R\s+)?777\s+/', 'chmod 777 on root path'),
    (r'\bchown\s+-R\s+\S+:(root|wheel)\s+/', 'chown -R to root on system paths'),
    (r'\bgit\s+push\s+(-[a-zA-Z]*f[a-zA-Z]*|--force)\b', 'git push --force'),
    (r'\bgit\s+push\s+.*--delete\b', 'git push --delete'),
    (r'\bgit\s+reset\s+--hard\b', 'git reset --hard'),
    (r'\bgit\s+clean\s+-[a-zA-Z]*[f][a-zA-Z]*d', 'git clean with force + directories'),
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', 'DROP TABLE/DATABASE/SCHEMA'),
    (r'\bTRUNCATE\s+(TABLE\s+)?', 'TRUNCATE TABLE'),
    (r'\bDELETE\s+FROM\s+\S+(?!\s+WHERE\b)', 'DELETE FROM without WHERE clause'),
    (r'\bALTER\s+TABLE\s+\S+\s+DROP\b', 'ALTER TABLE DROP'),
    (r'\biptables\s+-F\b', 'iptables flush all rules'),
    (r'\biptables\s+-P\s+\w+\s+ACCEPT\b', 'iptables set default ACCEPT'),
    (r'\bshutdown\b', 'system shutdown'),
    (r'\breboot\b', 'system reboot'),
    (r'\bhalt\b', 'system halt'),
    (r'\bpoweroff\b', 'system poweroff'),
    (r'\binit\s+[06]\b', 'init runlevel 0/6'),
    (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', 'fork bomb'),
    (r'\bwhile\s+true\s*;\s*do\b.*>(/dev/null|&\s*/dev/null)', 'infinite loop with redirection'),
]

WARNING_PATTERNS = [
    (r'\brm\s+', 'rm command detected'),
    (r'\bgit\s+stash\s+drop\b', 'git stash drop'),
    (r'\bgit\s+branch\s+-D\b', 'git branch -D'),
    (r'\bDROP\s+INDEX\b', 'DROP INDEX'),
]

def log_event(command, reason, project_path, action):
    os.makedirs(HOOKS_DIR, exist_ok=True)
    ts = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps({"timestamp": ts, "command": command, "reason": reason, "project_path": project_path, "action": action}) + '\n')

def check_command(cmd, project_path):
    cmd = cmd.strip()
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            log_event(cmd, reason, project_path, "BLOCKED")
            return {"block": True, "msg": f"BLOCKED: {reason}\n  Command: {cmd}\n  This command could cause irreversible damage."}
    for pattern, reason in WARNING_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            log_event(cmd, reason, project_path, "WARNING")
            return {"block": False, "warning": f"WARNING: {reason}\n  Command: {cmd}\n  Proceeding with caution."}
    return {"block": False}

def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        print(json.dumps({"continue": True})); sys.exit(0)
    if data.get("tool_name") != "Bash":
        print(json.dumps({"continue": True})); sys.exit(0)
    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd:
        print(json.dumps({"continue": True})); sys.exit(0)
    project_path = os.getenv("CLAUDE_PROJECT_DIR", os.getcwd())
    result = check_command(cmd, project_path)
    if result.get("block"):
        print(json.dumps({"continue": False, "reason": result["msg"]}))
    elif result.get("warning"):
        print(json.dumps({"continue": True, "hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow", "permissionDecisionReason": result["warning"]}}))
    else:
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
