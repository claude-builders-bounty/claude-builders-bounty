#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: block dangerous bash commands.

Install: copy to ~/.claude/hooks/pre-tool-use-safety.py
Register in ~/.claude/settings.json:
  {
    "hooks": {
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use-safety.py" }]
        }
      ]
    }
  }

On detection: writes a JSON response to stdout instructing Claude to stop
and logs the blocked attempt to ~/.claude/hooks/blocked.log.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Block patterns — (label, compiled-regex)
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Recursive force-remove — must start with rm command to avoid false positives
    # Matches: rm -rf, rm -fr, rm -rfv, rm -Rfv, rm --recursive --force, etc.
    # Uses two alternations to catch flags with r+f or f+r in any order.
    (
        "rm -rf (recursive force delete)",
        re.compile(r"\brm\b(?:\s+\S+)*\s+-\w*r\w*f\w*|\brm\b(?:\s+\S+)*\s+-\w*f\w*r\w*", re.I),
    ),
    # DROP TABLE (SQL)
    (
        "DROP TABLE (destructive SQL)",
        re.compile(r"\bDROP\s+TABLE\b", re.I),
    ),
    # TRUNCATE TABLE (SQL)
    (
        "TRUNCATE (destructive SQL)",
        re.compile(r"\bTRUNCATE\b", re.I),
    ),
    # DELETE FROM without a WHERE clause
    (
        "DELETE FROM without WHERE (destructive SQL)",
        re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.I | re.S),
    ),
    # git push --force / -f (overwrites remote history)
    # Use lookahead to avoid matching --force-with-lease (which is safer)
    (
        "git push --force (overwrites remote history)",
        re.compile(r"\bgit\s+push\b.*(?:--force(?![-\w])|-f\b)", re.I),
    ),
]


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def _log_blocked(command: str, reason: str, project: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{ts}] BLOCKED | project={project!r} | reason={reason!r} | command={command!r}\n"
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed input — do not interfere
        sys.exit(0)

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    project_dir = payload.get("cwd", os.getcwd())

    # Only inspect Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check each danger pattern
    for label, pattern in _PATTERNS:
        if pattern.search(command):
            _log_blocked(command, label, project_dir)

            # Output the hook response that tells Claude to stop
            response = {
                "decision": "block",
                "reason": (
                    f"🚫 Blocked by pre-tool-use safety hook.\n\n"
                    f"**Reason:** {label}\n\n"
                    f"**Command:** `{command}`\n\n"
                    f"This command pattern is considered destructive and has been blocked. "
                    f"If you intended this action, please ask the user to confirm and run it manually."
                ),
            }
            print(json.dumps(response))
            sys.exit(0)

    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
