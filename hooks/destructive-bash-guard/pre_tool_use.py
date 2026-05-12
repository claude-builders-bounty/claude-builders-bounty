#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Destructive Bash Command Guard

Blocks dangerous bash commands before Claude Code executes them.
Follows the Claude Code hooks protocol (stdin JSON → stdout JSON + exit code).

Blocked patterns:
  - rm -rf / rm --no-preserve-root
  - DROP TABLE / DROP DATABASE
  - TRUNCATE (SQL)
  - DELETE FROM without WHERE
  - git push --force / git push -f

Logs every blocked attempt to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Pattern definitions: (compiled_regex, reason_string)
# ---------------------------------------------------------------------------
BLOCKED_PATTERNS = [
    # rm -rf / rm --no-preserve-root
    (re.compile(r"\brm\s+.*-[a-zA-Z]*f.*\b", re.IGNORECASE),
     "rm with -f flag (destructive delete)"),

    (re.compile(r"\brm\s+.*--no-preserve-root\b", re.IGNORECASE),
     "rm --no-preserve-root (dangerous root deletion)"),

    # SQL: DROP TABLE / DROP DATABASE
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "DROP TABLE/DATABASE/SCHEMA (irreversible database operation)"),

    # SQL: TRUNCATE
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?", re.IGNORECASE),
     "TRUNCATE (wipes all table rows)"),

    # SQL: DELETE FROM without WHERE
    (re.compile(r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", re.IGNORECASE),
     "DELETE FROM without WHERE (deletes all rows)"),

    # git push --force / git push -f
    (re.compile(r"\bgit\s+push\b.*--force\b", re.IGNORECASE),
     "git push --force (overwrites remote history)"),

    (re.compile(r"\bgit\s+push\b.*\s-f\b", re.IGNORECASE),
     "git push -f (overwrites remote history)"),
]

# Allowed pattern overrides (e.g., "rm -rf" in a docker/container context)
# Not currently used, but can be extended.
ALLOWED_OVERRIDES = []

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """Append a blocked-attempt record to the log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"[{timestamp}] project='{project_path}' | "
        f"reason='{reason}' | command='{command}'\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry)


def check_command(command: str) -> list[str]:
    """Return a list of reasons the command should be blocked. Empty = safe."""
    reasons = []
    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(command):
            # Check if any override applies
            overridden = False
            for override in ALLOWED_OVERRIDES:
                if override.search(command):
                    overridden = True
                    break
            if not overridden:
                reasons.append(reason)
    return reasons


def main() -> None:
    # 1. Read stdin JSON from Claude Code
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — pass through
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Malformed input — fail safe, allow through
        sys.exit(0)

    # 2. Only intercept Bash tool calls
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    project_path = data.get("cwd", os.getcwd())

    # 3. Check against blocked patterns
    reasons = check_command(command)

    if not reasons:
        # Safe command — allow through (exit 0, no output)
        sys.exit(0)

    # 4. Log the blocked attempt
    log_blocked(command, "; ".join(reasons), project_path)

    # 5. Output deny decision + exit code 2 to block execution
    reason_text = "Blocked: " + "; ".join(reasons)
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason_text,
        }
    }

    # Print JSON to stdout (Claude Code reads this)
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")

    # Also write human-readable reason to stderr (shown to model)
    print(
        f"⛔ Destructive command blocked: {reason_text}\n"
        f"   Command: {command}\n"
        f"   Logged to: {LOG_FILE}",
        file=sys.stderr,
    )

    # Exit code 2 = block tool execution + send stderr to model
    sys.exit(2)


if __name__ == "__main__":
    main()
