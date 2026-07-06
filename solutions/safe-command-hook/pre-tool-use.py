#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook -- blocks destructive bash commands.
Place in ~/.claude/hooks/pre-tool-use.py to activate.
"""
import re, os, sys, json, datetime

BLOCKED_PATTERNS = [
    (r"\brm\s+-rf\b", "rm -rf"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE"),
    (r"\bgit\s+push\s+--force\b", "git push --force"),
    (r"\bgit\s+push\s+-f\b", "git push -f"),
    (r"\bTRUNCATE\b", "TRUNCATE table"),
    (r"\bDELETE\s+FROM\b(?!.*\s+WHERE\b)", "DELETE without WHERE"),
    (r"\bdd\s+if=.*\sof=", "dd raw device write"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def check_command(cmd):
    for pat, desc in BLOCKED_PATTERNS:
        if re.search(pat, cmd, re.IGNORECASE):
            return desc
    return None

def main():
    try:
        payload = json.loads(sys.stdin.read())
    except:
        sys.exit(0)
    cmd = ""
    if isinstance(payload, dict):
        cmd = payload.get("command", "") or payload.get("input", "") or str(payload)
    elif isinstance(payload, str):
        cmd = payload
    result = check_command(cmd)
    if result:
        ts = datetime.datetime.now().isoformat()
        entry = json.dumps({"ts": ts, "cmd": cmd[:200], "reason": result})
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(entry + chr(10))
        print("BLOCKED: " + result)
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
