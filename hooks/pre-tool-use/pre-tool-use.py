#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks dangerous bash commands.

Installation: mkdir -p ~/.claude/hooks/ && cp this_file ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
"""

import json, os, re, sys
from datetime import datetime

BLOCKLIST = [
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s*/?\b', 'Dangerous recursive force delete'),
    (r'(?i)\bgit\s+push\s+(--force|-f)\b', 'Force push blocked — use --force-with-lease'),
    (r'(?i)\bgit\s+reset\s+--hard\b', 'Hard reset blocked — will discard changes'),
    (r'(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b', 'DROP statement blocked'),
    (r'(?i)\bTRUNCATE\b', 'TRUNCATE blocked'),
    (r'(?i)\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'DELETE without WHERE blocked'),
    (r'(?i)\bUPDATE\s+\w+\s+SET\b(?!.*\bWHERE\b)', 'UPDATE without WHERE blocked'),
    (r'(?i)\b(?:shutdown|reboot|halt|poweroff)\b', 'System shutdown/reboot blocked'),
    (r'(?i)\bdd\s+if=', 'dd blocked — direct disk write'),
    (r'(?i)\bmkfs\.\w+\b', 'Filesystem creation blocked'),
    (r'(?i)\bchmod\s+-?R?\s*0\b', 'chmod 0 blocked'),
    (r'(?i)\bkill\s+-9\b', 'SIGKILL blocked — use targeted termination'),
    (r'(?i)\bsudo\s+rm\s+-rf\b', 'sudo recursive delete blocked'),
    (r'(?i)\bapt\s+(remove|purge|autoremove)\b', 'Package removal blocked'),
    (r'(?i)\bpip\s+uninstall\b', 'pip uninstall blocked'),
    (r'(?i)\bnpm\s+(uninstall|remove|rm|prune)\b', 'npm uninstall blocked'),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        return {"is_allowed": True}

    tool = payload.get("tool", {})
    if tool.get("name") != "Bash":
        return {"is_allowed": True}

    cmd = tool.get("input", {}).get("command", "") if isinstance(tool.get("input"), dict) else ""
    for pattern, reason in BLOCKLIST:
        if re.search(pattern, cmd):
            _log_block(cmd, reason)
            return {
                "is_allowed": False,
                "error": f"⛔ **Blocked**: {reason}\n\nIf intentional, prefix with `#allow`.",
            }
    return {"is_allowed": True}

def _log_block(cmd, reason):
    try:
        os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] {reason} | {os.getcwd()} | {cmd[:200]}\n")
    except Exception:
        pass

if __name__ == "__main__":
    print(json.dumps(main()))
