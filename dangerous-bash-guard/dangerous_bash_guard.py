#!/usr/bin/env python3
"""
dangerous-bash-guard.py — Claude Code PreToolUse hook that blocks dangerous bash commands.

Reads JSON input from stdin (Claude Code hook protocol), inspects the Bash tool command,
and returns a deny decision if it matches any dangerous pattern.

Exit codes:
  0 = allow (no dangerous pattern detected)
  0 = deny (outputs JSON with permissionDecision: "deny")

Blocked patterns:
  - rm -rf / rm -r -f / rm -fr (recursive force delete)
  - DROP TABLE / DROP DATABASE (SQL destruction)
  - git push --force / git push -f (force push)
  - TRUNCATE TABLE? (SQL truncation)
  - DELETE FROM without WHERE clause (unconditional deletion)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Dangerous Pattern Definitions ─────────────────────────────────

DANGEROUS_PATTERNS = [
    {
        "name": "Recursive force delete",
        "pattern": r"\brm\s+[^|&;]*-(?:[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\b",
        "reason": "'rm -rf' is a destructive recursive force delete. Use targeted deletions instead.",
        "severity": "critical",
    },
    {
        "name": "Drop table/database",
        "pattern": r"(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA)\b",
        "reason": "DROP TABLE/DATABASE is irreversible. Use migrations or soft deletes instead.",
        "severity": "critical",
    },
    {
        "name": "Force push",
        "pattern": r"\bgit\s+push\s+[^|&;]*?(?:--force|-f)\b",
        "reason": "'git push --force' rewrites remote history. Use '--force-with-lease' or rebase instead.",
        "severity": "high",
    },
    {
        "name": "Truncate table",
        "pattern": r"(?i)\bTRUNCATE\s+(TABLE\s+)?[\w\"`']",
        "reason": "TRUNCATE removes all rows without logging. Use DELETE with WHERE clause instead.",
        "severity": "high",
    },
    {
        "name": "Delete without WHERE",
        "pattern": r"(?i)\bDELETE\s+FROM\s+[\w\"`']+\s*;(?!.*\bWHERE\b)",
        "reason": "DELETE FROM without WHERE clause deletes all rows. Add a WHERE clause.",
        "severity": "high",
    },
    # Note: we do NOT blanket-block "DELETE FROM" because it may have a WHERE clause.
    # The strict pattern above handles the semicolon-terminated case without WHERE.
]


# ── Logging ───────────────────────────────────────────────────────

def get_log_path() -> Path:
    """Return the path to the blocked.log file."""
    # Respect CLAUDE_PROJECT_DIR if set, otherwise ~/.claude/hooks/
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "")
    if project_dir:
        log_dir = Path(project_dir) / ".claude" / "hooks"
    else:
        log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "blocked.log"


def log_blocked(command: str, reason: str, project_path: str = ""):
    """Append a blocked attempt to the log file."""
    log_path = get_log_path()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = json.dumps({
        "timestamp": timestamp,
        "command": command,
        "reason": reason,
        "project_path": project_path,
    }, ensure_ascii=False)
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except OSError as e:
        # Log failure should never block the hook itself
        print(f"[dangerous-bash-guard] Warning: could not write log: {e}", file=sys.stderr)


# ── Core Logic ────────────────────────────────────────────────────

def check_command(command: str) -> dict | None:
    """
    Check a bash command against all dangerous patterns.
    Returns the first matching pattern dict, or None if safe.
    """
    # Special case: --force-with-lease is safe, skip force push check
    if re.search(r"\bgit\s+push\s+[^|&;]*--force-with-lease\b", command):
        # Allow --force-with-lease, but still check other patterns
        for pattern_def in DANGEROUS_PATTERNS:
            if pattern_def["name"] == "Force push":
                continue
            if re.search(pattern_def["pattern"], command):
                return pattern_def
        return None

    for pattern_def in DANGEROUS_PATTERNS:
        if re.search(pattern_def["pattern"], command):
            return pattern_def
    return None


def build_deny_output(reason: str, pattern_name: str, command: str) -> dict:
    """Build the JSON output for a denied command."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"[dangerous-bash-guard] Blocked: {pattern_name}. "
                f"{reason} "
                f"(attempted command: {command[:200]})"
            ),
        }
    }


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse input, allow by default (fail-open for safety)
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", os.environ.get("CLAUDE_PROJECT_DIR", ""))

    # Only check Bash tool calls
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check against dangerous patterns
    match = check_command(command)
    if match:
        # Log the blocked attempt
        log_blocked(command, match["reason"], project_path)
        # Return deny decision
        output = build_deny_output(match["reason"], match["name"], command)
        json.dump(output, sys.stdout)
        sys.stdout.write("\n")
        # Exit 0 with JSON output = deny
        sys.exit(0)

    # No dangerous pattern found — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
