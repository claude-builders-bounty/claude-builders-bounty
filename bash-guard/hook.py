#!/usr/bin/env python3
"""
bash-guard — Claude Code pre-tool-use hook that blocks destructive bash commands.

Install: cp hook.py ~/.claude/hooks/
Claude Code reads this before executing any tool. The hook receives JSON on stdin
and must emit JSON on stdout.

Blocked patterns:
  - rm -rf
  - DROP TABLE
  - git push --force
  - TRUNCATE
  - DELETE FROM without WHERE
"""
import json, sys, os, re, datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Destructive patterns to block
BLOCKED = [
    (r'rm\s+-rf', "rm -rf is destructive — use rm -i or specify exact files"),
    (r'DROP\s+TABLE', "DROP TABLE is destructive — backup first or use soft-delete"),
    (r'git\s+push\s+.*--force', "git push --force overwrites remote history — use --force-with-lease"),
    (r'TRUNCATE\s+', "TRUNCATE is destructive — use DELETE with WHERE or backup first"),
]

# DELETE FROM without WHERE
DELETE_WITHOUT_WHERE = re.compile(r'DELETE\s+FROM\s+\w+\s*;?$', re.I)

def log_block(command, reason, cwd):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    with open(LOG_FILE, "a") as f:
        f.write(f"{ts} | {command} | {cwd} | BLOCKED: {reason}\n")

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON on stdin"}))
        sys.exit(1)
    
    tool_use = data.get("tool_use", {})
    if tool_use.get("name") != "bash":
        # Not a bash command — pass through unchanged
        print(json.dumps(data))
        return
    
    command = tool_use.get("input", {}).get("command", "")
    if not command:
        print(json.dumps(data))
        return
    
    cwd = os.getcwd()
    
    # Check blocked patterns
    for pattern, reason in BLOCKED:
        if re.search(pattern, command, re.I):
            log_block(command, reason, cwd)
            safe_cmd = f"echo 'BLOCKED by bash-guard: {reason}. Command was: {command}'"
            output = {
                "tool_use": {
                    "name": "bash",
                    "input": {"command": safe_cmd}
                },
                "message": f"⚠️ bash-guard blocked destructive command: {command}\nReason: {reason}"
            }
            print(json.dumps(output))
            return
    
    # Check DELETE FROM without WHERE
    if DELETE_WITHOUT_WHERE.search(command):
        reason = "DELETE FROM without WHERE clause deletes all rows — add a WHERE clause"
        log_block(command, reason, cwd)
        safe_cmd = f"echo 'BLOCKED by bash-guard: {reason}. Command was: {command}'"
        output = {
            "tool_use": {
                "name": "bash",
                "input": {"command": safe_cmd}
            },
            "message": f"⚠️ bash-guard blocked destructive command: {command}\nReason: {reason}"
        }
        print(json.dumps(output))
        return
    
    # Safe command — pass through unchanged
    print(json.dumps(data))

if __name__ == "__main__":
    main()
