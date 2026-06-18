#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Blocks Destructive Bash Commands

Installed to ~/.claude/hooks/pre-tool-use/block_destructive_commands.py

Reads the tool use JSON from stdin, checks if the command contains
destructive patterns, and returns a deny decision if so.

Patterns blocked:
  - rm -rf (recursive force delete)
  - DROP TABLE (SQL destructive)
  - git push --force (force push)
  - TRUNCATE (SQL destructive)
  - DELETE FROM without WHERE clause (SQL destructive)

Logs all blocked attempts to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

DESTRUCTIVE_PATTERNS = [
    (r'\brm\s+-r[f]?\b', 'rm -rf (recursive forced deletion)'),
    (r'\bDROP\s+TABLE\b', 'DROP TABLE (SQL table destruction)'),
    (r'\bgit\s+push\s+--force\b', 'git push --force (force push overwrites history)'),
    (r'\bTRUNCATE\b', 'TRUNCATE (SQL table data destruction)'),
    (r'\bDELETE\s+FROM\b(?!\s*\S+\s+WHERE\b)', 'DELETE FROM without WHERE clause (unconditional row deletion)'),
]

# ── Hook Logic ─────────────────────────────────────────────────────

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command contains destructive patterns.
    Returns (is_blocked, reason).
    """
    for pattern, description in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, description
    return False, ""


def log_blocked(command: str, reason: str, project_path: str):
    """Log a blocked command attempt to the log file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "project_path": project_path,
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — allow (shouldn't happen, but be safe)
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return

        payload = json.loads(raw)

        # Extract the tool input from the hook payload
        tool_input = payload.get("toolInput", {}) or {}
        command = tool_input.get("cmd", "") or ""
        tool_name = payload.get("toolName", "")
        project_path = payload.get("projectPath", os.getcwd())

        # Only check Bash and ExecuteCommand tools
        if tool_name not in ("Bash", "ExecuteCommand"):
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return

        if not command:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
            return

        # Check for destructive patterns
        is_blocked, reason = check_command(command)

        if is_blocked:
            log_blocked(command, reason, project_path)
            result = {
                "hookSpecificOutput": {
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"⛔ Command blocked by safety hook: {reason}\n\n"
                        f"Attempted: {command[:200]}\n"
                        f"Logged to: {LOG_FILE}\n\n"
                        f"If this was intentional, use an explicit safe alternative:\n"
                        f"  - For rm -rf: delete files one by one, or use a trash directory\n"
                        f"  - For destructive SQL: add a WHERE clause or use SAFE_UPDATE_MODE\n"
                        f"  - For git push --force: use git push --force-with-lease instead"
                    ),
                }
            }
            print(json.dumps(result))
        else:
            print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))

    except json.JSONDecodeError:
        # Invalid JSON — allow to avoid breaking Claude
        print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))
    except Exception:
        # Any other error — allow to avoid breaking Claude
        print(json.dumps({"hookSpecificOutput": {"permissionDecision": "allow"}}))


if __name__ == "__main__":
    main()
