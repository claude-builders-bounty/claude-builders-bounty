#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands

Intercepts dangerous bash commands before Claude Code executes them.
Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE

Installation:
  1. Copy this file to ~/.claude/hooks/pre-tool-use-block-destructive.py
  2. Make executable: chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py
  3. Add to ~/.claude/settings.json hooks configuration (see README.md)

Follows Claude Code hooks format as documented at:
https://docs.anthropic.com/claude-code/hooks
"""

import json
import re
import sys
import os
from datetime import datetime, timezone

# ─── Configuration ──────────────────────────────────────────────

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are ALWAYS blocked
BLOCKED_PATTERNS = [
    # rm -rf variants
    (r'\brm\s+.*-.*[rR].*f\b', 'rm -rf or rm -fr: recursive force delete'),
    (r'\brm\s+.*-.*[fF].*r\b', 'rm -rf or rm -fr: recursive force delete'),
    (r'\brm\s+-rf\b', 'rm -rf: recursive force delete'),
    (r'\brm\s+-fr\b', 'rm -rf: recursive force delete'),

    # SQL destructive commands
    (r'\bDROP\s+TABLE\b', 'DROP TABLE: destroys database table'),
    (r'\bDROP\s+DATABASE\b', 'DROP DATABASE: destroys entire database'),
    (r'\bDROP\s+SCHEMA\b', 'DROP SCHEMA: destroys database schema'),
    (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE: deletes all rows'),
    (r'\bTRUNCATE\b(?!\s+only)', 'TRUNCATE: deletes all rows from table'),

    # DELETE FROM without WHERE clause
    (r'\bDELETE\s+FROM\b(?:(?!WHERE\b).)*$', 'DELETE FROM without WHERE: deletes all rows'),
    (r'\bDELETE\s+FROM\b(?:(?!WHERE\b).)*\s*;\s*$', 'DELETE FROM without WHERE: deletes all rows'),

    # Git force push
    (r'\bgit\s+push\s+.*--force\b', 'git push --force: overwrites remote history'),
    (r'\bgit\s+push\s+-f\b', 'git push -f: overwrites remote history'),
    (r'\bgit\s+push\s+.*--force-with-lease\b', 'git push --force-with-lease: forced push (safer but still risky)'),

    # System destruction
    (r'\b:\(\)\{\s*:\|\:&\s*\}', 'Fork bomb detected'),
    (r'\bmkfs\b', 'mkfs: formats filesystem'),
    (r'\bdd\s+.*of=/dev/', 'dd to device: can destroy disk data'),
    (r'\bshutdown\b', 'shutdown: halts the system'),
    (r'\breboot\b', 'reboot: restarts the system'),
    (r'\bhalt\b', 'halt: stops the system'),

    # Permission changes on critical dirs
    (r'\bchmod\s+.*-R\s+777\s+/', 'chmod 777 -R on root: dangerous permission change'),
    (r'\bchown\s+.*-R\s+\w+\s+/', 'chown -R on root: dangerous ownership change'),
]

# Compile patterns for performance (case-insensitive for SQL, case-sensitive for shell)
COMPILED_PATTERNS = []
for pattern, reason in BLOCKED_PATTERNS:
    sql_keywords = any(kw in pattern for kw in ['DROP', 'TRUNCATE', 'DELETE', 'FROM', 'WHERE'])
    flags = re.IGNORECASE if sql_keywords else 0
    try:
        COMPILED_PATTERNS.append((re.compile(pattern, flags), reason))
    except re.error:
        pass  # Skip invalid patterns


# ─── Logging ────────────────────────────────────────────────────

def log_blocked(command: str, reason: str, project_path: str = ""):
    """Log blocked attempt to the audit log."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_dir = os.path.dirname(LOG_FILE)
    os.makedirs(log_dir, exist_ok=True)

    log_entry = json.dumps({
        "timestamp": timestamp,
        "command": command.strip(),
        "reason": reason,
        "project_path": project_path,
    })

    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")


# ─── Main Hook Logic ───────────────────────────────────────────

def check_command(command: str) -> tuple[bool, str]:
    """
    Check if a command should be blocked.
    Returns (is_blocked, reason).
    """
    if not command or not command.strip():
        return False, ""

    # Normalize whitespace for matching
    normalized = ' '.join(command.split())

    for compiled_pattern, reason in COMPILED_PATTERNS:
        if compiled_pattern.search(normalized):
            return True, reason

    return False, ""


def main():
    """Main hook entry point. Reads stdin for tool use context."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # If we can't parse input, allow the command (fail open for safety)
        sys.exit(0)

    # Extract the command from the hook input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only intercept bash/shell commands
    if tool_name not in ("bash", "shell"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Get project path for logging
    project_path = input_data.get("project_path", os.getcwd())

    # Check the command
    is_blocked, reason = check_command(command)

    if is_blocked:
        log_blocked(command, reason, project_path)

        # Output blocking response for Claude Code
        response = {
            "decision": "block",
            "reason": f"🚫 Command blocked by security hook: {reason}\n\n"
                      f"Command: `{command.strip()}`\n\n"
                      f"If you're sure this is safe, the user can run it directly in the terminal.\n"
                      f"Blocked attempt logged to {LOG_FILE}"
        }
        print(json.dumps(response))
        sys.exit(0)
    else:
        # Allow the command
        sys.exit(0)


if __name__ == "__main__":
    main()
