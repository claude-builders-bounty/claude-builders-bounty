#!/usr/bin/env python3
"""pre-tool-use hook: block destructive bash commands.

Reads JSON from stdin (Claude Code hook format), inspects the bash command,
and blocks dangerous patterns by exiting non-zero with a reason on stdout.

Dangerous patterns:
  rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE

Every blocked attempt is logged to ~/.claude/hooks/blocked.log
with: timestamp, attempted command, project path.
"""
import sys
import json
import os
import re
from datetime import datetime

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

DANGEROUS_PATTERNS = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*\s+)*(--?r|--?f|-rf|-fr)\b"), "rm -rf (recursive force delete)"),
    (re.compile(r"\brm\s+-rf\b"), "rm -rf (recursive force delete)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE (destroys a table)"),
    (re.compile(r"\bgit\s+push\s+(--?f|--?force|origin\s+\w+\s*:\s*\w+)\b", re.IGNORECASE), "git push --force (overwrites remote history)"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE (empties a table)"),
    (re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE), "DELETE FROM without WHERE (deletes all rows)"),
]

def log_blocked(command: str, project: str, reason: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with open(LOG_PATH, "a") as f:
        f.write(f"{ts} | project={project} | reason={reason} | cmd={command}\n")

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # not our hook event, allow

    tool = data.get("tool_name", "")
    if tool != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    project = data.get("cwd", data.get("project_path", "unknown"))

    for pattern, reason in DANGEROUS_PATTERNS:
        # special-case DELETE FROM: only block if no WHERE clause
        if "DELETE FROM" in reason.upper():
            if re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE) and not re.search(r"\bWHERE\b", command, re.IGNORECASE):
                log_blocked(command, project, reason)
                out = {
                    "decision": "block",
                    "reason": f"Blocked: {reason}. Add a WHERE clause or confirm intentionally.",
                }
                print(json.dumps(out))
                sys.exit(1)
        elif pattern.search(command):
            log_blocked(command, project, reason)
            out = {
                "decision": "block",
                "reason": f"Blocked: {reason}. This is a destructive operation and was prevented by the safety hook.",
            }
            print(json.dumps(out))
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
