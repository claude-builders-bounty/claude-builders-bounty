#!/usr/bin/env python3
"""
pre-tool-use hook: blocks destructive bash commands before execution.

Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM (no WHERE)
Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json, os, re, sys
from datetime import datetime, timezone

LOG_DIR = os.path.expanduser("~/.claude/hooks")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

DANGEROUS_PATTERNS = [
    (r'\brm\s+.*-rf\b', "rm -rf (recursive force delete)"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE (irreversible schema deletion)"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE (irreversible database deletion)"),
    (r'\bgit\s+push\s+.*--force\b', "git push --force (overwrite remote history)"),
    (r'\bgit\s+push\s+.*-f\b', "git push -f (overwrite remote history)"),
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', "TRUNCATE (irreversible data wipe)"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?!.*WHERE\b)', "DELETE FROM without WHERE (full table wipe)"),
    (r'\bchmod\s+-R\s+777\b', "chmod -R 777 (world-writable exposure)"),
    (r'\b:(){ :|:& };:', "fork bomb detected"),
    (r'\bdd\s+if=.*of=/dev/', "dd writing to /dev/ device (disk destruction)"),
    (r'\bmkfs\.', "mkfs (filesystem creation = data loss)"),
    (r'\bgit\s+reset\s+--hard\b', "git reset --hard (irreversible working tree reset)"),
]

def is_dangerous(command: str) -> tuple[bool, str]:
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def log_blocked(command: str, reason: str, cwd: str):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": ts,
        "command": command,
        "reason": reason,
        "cwd": cwd
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    input_data = json.loads(sys.stdin.read())
    command = input_data.get("command", "")
    cwd = input_data.get("cwd", os.getcwd())

    dangerous, reason = is_dangerous(command)
    if not dangerous:
        print(json.dumps({"continue": True}))
        sys.exit(0)

    log_blocked(command, reason, cwd)
    print(json.dumps({
        "continue": False,
        "message": f"BLOCKED: {reason}. Command: `{command}`.\nThis action was intercepted by the safety hook. If you truly intend this, disable the hook or provide justification."
    }))

if __name__ == "__main__":
    main()