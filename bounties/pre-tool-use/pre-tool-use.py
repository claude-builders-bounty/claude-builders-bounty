#!/usr/bin/env python3
"""
pre-tool-use.py — Blocks destructive bash commands before they execute.

Place in ~/.claude/hooks/pre-tool-use.py (or any supported hook path).
Claude Code passes the command via stdin as a JSON object with a "command" key.

Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM (no WHERE)
Logs: every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json, os, re, sys, time

LOG = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOKS_DIR = os.path.dirname(LOG)

# ponytail: one pattern list, one log format
BLOCKED_PATTERNS = [
    (re.compile(r'\brm\s+-rf\b', re.IGNORECASE), "rm -rf is destructive"),
    (re.compile(r'\bdrop\s+table\b', re.IGNORECASE), "DROP TABLE destroys data"),
    (re.compile(r'\bgit\s+push\s+--force\b', re.IGNORECASE), "git push --force overwrites history"),
    (re.compile(r'\btruncate\s+\w+\b', re.IGNORECASE), "TRUNCATE removes all rows"),
    (re.compile(r'\bdelete\s+from\s+\w+\s*(?!\s*where)', re.IGNORECASE), "DELETE FROM without WHERE is unsafe"),
]

def main():
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        # Not a JSON hook call — pass through
        sys.exit(0)

    cmd = payload.get("command", "")
    if not cmd:
        sys.exit(0)

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(cmd):
            os.makedirs(HOOKS_DIR, exist_ok=True)
            with open(LOG, "a") as f:
                ts = time.strftime("%Y-%m-%dT%H:%M:%S")
                cwd = os.getcwd()
                f.write(f"[{ts}] BLOCKED | cwd:{cwd} | reason:{reason} | cmd:{cmd}\n")

            result = json.dumps({
                "is_error": True,
                "error_message": f"Blocked: {reason}. Use the project's safer alternative (migration scripts, CI-only push). Logged to {LOG}."
            })
            print(result)
            sys.exit(0)

    # Pass through: print nothing = Claude proceeds
    sys.exit(0)

if __name__ == "__main__":
    main()
