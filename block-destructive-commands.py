#!/usr/bin/env python3
"""
block-destructive-commands.py
A Claude Code PreToolUse hook that intercepts dangerous bash commands.

Blocks:
- rm -rf / rm --recursive --force
- DROP TABLE
- git push --force / git push -f
- TRUNCATE
- DELETE FROM without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log with:
- ISO 8601 timestamp
- Attempted command
- Project path (CWD)

Returns JSON to Claude Code's stdin with decision: "block" and a clear reason.

Installation:
    mkdir -p ~/.claude/hooks
    curl -o ~/.claude/hooks/block-destructive-commands.py \\
        https://raw.githubusercontent.com/TriggerXZ/block-destructive-commands/main/block-destructive-commands.py
    chmod +x ~/.claude/hooks/block-destructive-commands.py

Then add to ~/.claude/settings.json:
    {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "python3 ~/.claude/hooks/block-destructive-commands.py"
                        }
                    ]
                }
            ]
        }
    }
"""

import json
import re
import sys
import os
import datetime
from pathlib import Path

# Patterns that should ALWAYS be blocked (case-insensitive regex)
DANGEROUS_PATTERNS = [
    # rm -rf and variants
    (r'\brm\s+(-[a-zA-Z]*[rR][fF]|-[a-zA-Z]*[fF][rR]|-{0,2}recursive\s+--force|--recursive\s+-{0,2}force|-{0,2}force\s+--recursive)\b', 'recursive force delete (rm -rf)'),
    (r'\brm\s+-rf\b', 'rm -rf'),
    (r'\brm\s+--recursive\s+--force\b', 'rm --recursive --force'),
    # SQL: DROP TABLE
    (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
    # SQL: TRUNCATE
    (r'\bTRUNCATE\s+(TABLE\s+)?\w+', 'TRUNCATE'),
    # SQL: DELETE FROM without WHERE
    # Block when: followed by ;, end-of-string, end-of-quoted-string, or end-of-line
    (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$|"|\')', 'DELETE FROM without WHERE clause'),
    # git push --force / -f to any remote
    (r'\bgit\s+push\s+(-{1,2}f(?:orce)?\b|--force-with-lease\b)', 'git push --force'),
    (r'\bgit\s+push\s+--force-with-lease\b', 'git push --force-with-lease'),
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def is_dangerous(command: str):
    """Return (is_dangerous, reason) for the given command."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, None


def log_blocked(command: str, reason: str, project_path: str):
    """Append a blocked-attempt entry to blocked.log."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().isoformat(timespec='seconds')
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] project={project_path} | reason={reason} | command={command}\n")
    except OSError as e:
        # Don't crash the hook if logging fails — just print to stderr
        print(f"[block-destructive-commands] WARNING: could not write log: {e}", file=sys.stderr)


def main():
    # Claude Code passes hook input as JSON on stdin
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — allow (the hook was invoked without context)
            print(json.dumps({"decision": "allow"}))
            return
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[block-destructive-commands] WARNING: invalid JSON input: {e}", file=sys.stderr)
        # Fail open (allow) so a malformed input doesn't break the user's session
        print(json.dumps({"decision": "allow"}))
        return

    # Extract the bash command
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") or ""

    # Project path (cwd at time of invocation)
    project_path = (
        payload.get("cwd")
        or payload.get("project_path")
        or os.environ.get("PWD")
        or os.getcwd()
    )

    dangerous, reason = is_dangerous(command)
    if not dangerous:
        print(json.dumps({"decision": "allow"}))
        return

    # Log it
    log_blocked(command, reason, project_path)

    # Tell Claude Code to block
    response = {
        "decision": "block",
        "reason": (
            f"⛔ BLOCKED by block-destructive-commands hook: {reason}\n\n"
            f"Command: {command}\n\n"
            f"This pattern is on the block list because it can cause irreversible damage. "
            f"If you really need to run it, ask the user for explicit permission first "
            f"and have them run it manually outside of Claude Code."
        ),
    }
    print(json.dumps(response))


if __name__ == "__main__":
    main()
