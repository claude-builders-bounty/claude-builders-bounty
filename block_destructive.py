#!/usr/bin/env python3
import json, sys, re, os
from datetime import datetime
from pathlib import Path
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
BLOCKED = [
    (r"\brm\s+.*-[a-z]*r[a-z]*f", "rm -rf", "Destructive rm -rf will irreversibly delete files."),
    (r"\brm\s+-rf\b", "rm -rf", "Destructive rm -rf will irreversibly delete files."),
    (r"DROP\s+TABLE", "DROP TABLE", "DROP TABLE permanently deletes database tables."),
    (r"TRUNCATE\s+(TABLE)?", "TRUNCATE", "TRUNCATE permanently deletes all rows."),
    (r"git\s+push\s+.*--force", "git push --force", "git push --force overwrites remote history. Use --force-with-lease."),
    (r"git\s+push\s+.*\s-f(\s|$)", "git push -f", "git push -f overwrites remote history."),
]
def is_delete_no_where(cmd):
    for stmt in cmd.split(';'):
        if re.search(r"DELETE\s+FROM\s+\w+", stmt, re.I):
            if "WHERE" not in stmt.upper():
                return True
    return False
def main():
    try:
        data = json.load(sys.stdin)
    except:
        sys.exit(0)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    cmd = data.get("tool_input", {}).get("command", "")
    if not cmd: sys.exit(0)
    reason = None; name = None
    for pat, n, r in BLOCKED:
        flag = re.I if "DROP" in pat or "TRUNCATE" in pat else 0
        if re.search(pat, cmd, flag):
            reason=r; name=n; break
    if not reason and is_delete_no_where(cmd):
        reason="DELETE FROM without WHERE will delete ALL rows. Add WHERE clause."; name="DELETE without WHERE"
    if reason:
        ts=datetime.now().isoformat()
        cwd=data.get("cwd", os.getcwd())
        with open(LOG_FILE, "a") as f:
            f.write(f"[{ts}] BLOCKED:{name} | PATH:{cwd} | CMD:{cmd}\n")
        out={"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":f"BLOCKED ({name}): {reason} | CMD: {cmd} | Logged to ~/.claude/hooks/blocked.log"}}
        print(json.dumps(out))
        sys.exit(0)
if __name__ == "__main__": main()
