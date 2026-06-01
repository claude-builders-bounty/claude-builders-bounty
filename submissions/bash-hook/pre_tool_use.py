#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — 拦截危险 bash 命令
安装: cp hook.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
"""

import json, sys, os, re
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(HOOK_DIR, exist_ok=True)

DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\b", "rm -rf"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bgit\s+push\s+.*--force", "git push --force"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE"),
    (r"\bchmod\s+777\b", "chmod 777"),
    (r"\b:\s*\(\)\s*\{\s*:\s*\|\s*:\s*\}\s*;\s*:", "fork bomb"),
    (r"\bdd\s+if=", "dd disk write"),
    (r"\bmkfs\.", "mkfs format"),
]

def log_blocked(command, cwd="unknown"):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED | CWD: {cwd} | CMD: {command}\n")

def main():
    try:
        data = json.loads(sys.stdin.read())
    except:
        sys.exit(0)

    tool = data.get("tool_name", "")
    args = data.get("tool_input", {})

    if tool != "bash" and tool != "run_shell_command":
        sys.stdout.write(json.dumps({"continue": True}))
        return

    command = args.get("command", "")
    cwd = args.get("workdir", os.getcwd())

    for pattern, name in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_blocked(command, cwd)
            msg = f"🚫 BLOCKED: {name}\n   Command: {command}\n   This pattern is too dangerous. If you really need this, edit the hook at {__file__}"
            sys.stdout.write(json.dumps({
                "continue": False,
                "reason": msg[:500]
            }))
            return

    sys.stdout.write(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
