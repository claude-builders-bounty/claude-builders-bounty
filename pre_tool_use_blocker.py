#!/usr/bin/env python3
"""pre_tool_use_blocker.py — Claude Code pre-tool-use hook.

Blocks destructive bash commands before they run.
Patterns blocked: rm -rf, DROP TABLE, git push --force, TRUNCATE,
DELETE FROM without WHERE, :(){ fork bomb, mkfs, dd if=, chmod -R 777 /, etc.

Logs every blocked attempt to ~/.claude/hooks/blocked.log with
timestamp, attempted command, and project path. Prints a clear reason
to stderr (which Claude Code surfaces to the model).

Exit code 0 = allow, 2 = block (per Claude Code hook contract).
"""
import sys
import os
import re
import json
import datetime

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# (compiled regex, human reason)
BLOCK_PATTERNS = [
    (re.compile(r"\brm\s+-rf\b|\brm\s+-fr\b|\brm\s+-r\s+-f\b", re.I), "recursive force delete (rm -rf)"),
    (re.compile(r"\bdrop\s+table\b", re.I), "DROP TABLE statement"),
    (re.compile(r"git\s+push\s+.*--force|git\s+push\s+-f\b", re.I), "force push (git push --force)"),
    (re.compile(r"\btruncate\b", re.I), "TRUNCATE statement"),
    (re.compile(r"delete\s+from\b(?!(.*\bwhere\b))", re.I | re.S), "DELETE FROM without a WHERE clause"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\&\s*:", re.I), "fork bomb"),
    (re.compile(r"\bdd\s+if=", re.I), "raw disk write (dd if=)"),
    (re.compile(r"\bmkfs\b", re.I), "filesystem format (mkfs)"),
    (re.compile(r"chmod\s+-R\s+777\s+/", re.I), "world-write on root (chmod -R 777 /)"),
]

def main():
    # Claude Code passes tool input as JSON on stdin for pre-tool-use.
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # can't parse -> allow (fail open, don't break workflows)

    tool = data.get("tool_name", "")
    cmd = ""
    if tool == "Bash":
        cmd = data.get("tool_input", {}).get("command", "")
    if not cmd:
        sys.exit(0)

    for rx, reason in BLOCK_PATTERNS:
        if rx.search(cmd):
            project = os.environ.get("PWD", "unknown")
            ts = datetime.datetime.now().isoformat()
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a") as f:
                f.write(f"{ts} | BLOCKED: {cmd} | project: {project} | reason: {reason}\n")
            print(f"[BLOCKED] Command not run: {reason}. "
                  f"This looks destructive and was stopped by the safety hook.", file=sys.stderr)
            sys.exit(2)  # block

    sys.exit(0)  # allow

if __name__ == "__main__":
    main()
