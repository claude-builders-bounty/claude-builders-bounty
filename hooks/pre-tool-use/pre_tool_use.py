#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash commands.

Reads tool-call JSON from stdin.  Blocks dangerous patterns and logs
every blocked attempt to ~/.claude/hooks/blocked.log.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# (compiled-regex, human-readable reason shown to Claude)
DANGEROUS = [
    (re.compile(r"\brm\s+-rf\b"), "rm -rf (recursive force delete)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE (destroys database table)"),
    (re.compile(r"\bgit\s+push\s+.*--force"), "git push --force (overwrites remote history)"),
    (re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?\w", re.IGNORECASE), "TRUNCATE (removes all rows)"),
]


def _delete_without_where(cmd: str) -> bool:
    """True when cmd contains DELETE FROM <table> without a WHERE clause."""
    if not re.search(r"\bDELETE\s+FROM\s+\S", cmd, re.IGNORECASE):
        return False
    return not re.search(r"\bWHERE\b", cmd, re.IGNORECASE)


def _log(cmd: str, project: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with open(LOG, "a") as fh:
        fh.write(f"[{ts}] project={project}  command={cmd}\n")


def main() -> None:
    # --- parse stdin --------------------------------------------------
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)                         # malformed input → allow

    if event.get("tool_name", "") != "Bash":
        sys.exit(0)                         # not a bash call → allow

    command = event.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    project = event.get("cwd", os.getcwd())

    # --- check patterns -----------------------------------------------
    reason = None
    for pat, msg in DANGEROUS:
        if pat.search(command):
            reason = msg
            break

    if not reason and _delete_without_where(command):
        reason = "DELETE FROM without WHERE (would delete all rows)"

    if not reason:
        sys.exit(0)                         # safe command → allow

    # --- block --------------------------------------------------------
    _log(command, project)

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command: {reason}.  "
                f"If this is intentional, modify the command to be explicitly safe."
            ),
        }
    }))

    sys.exit(2)   # 2 = hook blocked (distinct from 1 = hook crashed)


if __name__ == "__main__":
    main()
