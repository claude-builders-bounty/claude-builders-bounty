#!/usr/bin/env python3
"""
Dangerous Command Blocker - Claude Code pre-tool-use hook.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
"""
import json, os, re, sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    (re.compile(r'\brm\s+(-[rfR]+|-[rf]+\s+-[rfR]+)\s+'), "rm -rf (recursive force delete)"),
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE (database table deletion)"),
    (re.compile(r'\bgit\s+push\s+.*--force\b'), "git push --force (force push)"),
    (re.compile(r'\bgit\s+push\s+.*\s-f\b'), "git push -f (force push)"),
    (re.compile(r'\bTRUNCATE\b', re.IGNORECASE), "TRUNCATE (database truncation)"),
]

def has_where_clause(cmd):
    dm = re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE)
    if dm:
        return bool(re.search(r'\bWHERE\b', cmd[dm.end():], re.IGNORECASE))
    return True

def check(cmd):
    for pat, desc in DANGEROUS_PATTERNS:
        if pat.search(cmd):
            return (True, f"Blocked: {desc}")
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.IGNORECASE) and not has_where_clause(cmd):
        return (True, "Blocked: DELETE FROM without WHERE clause (mass deletion)")
    return (False, "")

def main():
    try:
        inp = json.loads(sys.stdin.read())
    except:
        return
    tn = (inp.get("tool_name") or inp.get("toolName") or "").lower()
    if tn not in ("bash", "terminal", "shell", "command_run"):
        return
    ti = inp.get("tool_input") or inp.get("toolInput") or {}
    cmd = ti.get("command", "") if isinstance(ti, dict) else (ti if isinstance(ti, str) else "")
    if not cmd:
        return
    bad, reason = check(cmd)
    if not bad:
        return
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proj = os.getcwd()
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {reason}\n")
        f.write(f"  Command: {cmd}\n")
        f.write(f"  Project: {proj}\n")
        f.write(f"  ---\n")
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason}. If needed, run manually outside Claude Code.",
            "additionalContext": f"The command `{cmd}` was blocked. Reason: {reason}"
        }
    }))

if __name__ == "__main__":
    main()
