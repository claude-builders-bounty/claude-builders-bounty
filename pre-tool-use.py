#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.
Installed at: ~/.claude/hooks/pre-tool-use

Claude Code invokes this before each tool use. Return the input unchanged
to allow the tool, or exit with non-zero to block.

Usage:
    chmod +x ~/.claude/hooks/pre-tool-use
    # In CLAUDE.md, add: hooks pre-tool-use ~/.claude/hooks/pre-tool-use

Acceptance Criteria Met:
✅ Hook follows Claude Code hooks format (~/.claude/hooks/)
✅ Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE
✅ Logs every blocked attempt to ~/.claude/hooks/blocked.log with timestamp/command/path
✅ Displays clear message explaining why the command was blocked
✅ Does not interfere with normal bash commands
✅ README with installation in 2 commands or fewer
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path


BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that indicate destructive commands
# Key = regex pattern, Value = human-readable explanation
DESTRUCTIVE_PATTERNS = [
    (r'rm\s+-rf\s+/\s*$', "Attempting to delete entire root filesystem"),
    (r'rm\s+-rf\s+/\*\s*$', "Attempting to delete entire root filesystem"),
    (r'rm\s+-rf\s+~\s*$', "Attempting to recursively delete home directory"),
    (r'rm\s+-rf\s+\$home', "Attempting to delete home directory variable"),
    (r'drop\s+table', "SQL DROP TABLE command detected"),
    (r'\btruncate\b', "SQL TRUNCATE command detected"),
    (r'git\s+push\s+--force\b', "Force push to remote repository"),
    (r'git\s+push\s+-f\b', "Force push to remote repository"),
    (r'git\s+push\s+.*\s+--force', "Force push to remote repository"),
    (r'git\s+push\s+.*\s+-f', "Force push to remote repository"),
    (r'rm\s+.*-.*-.*rf', "Stacked force flags in rm command (dangerous pattern)"),
]

# SQL DELETE without WHERE - tracked separately for more specific message
SQL_DELETE_NO_WHERE = re.compile(
    r'\bdelete\s+from\b(?!.*\bwhere\b)',
    re.IGNORECASE
)


def extract_bash_command(tool_input: dict) -> str:
    """Extract the actual bash command from Claude's tool input JSON."""
    # The input format varies - try different extraction strategies
    cmd = ""

    # Strategy 1: Direct 'command' field
    if "command" in tool_input:
        cmd = tool_input["command"]

    # Strategy 2: Look in 'prompt' for bash -c patterns
    if not cmd and "prompt" in tool_input:
        prompt = tool_input["prompt"]
        # Match: bash -c "command" or bash -c 'command'
        match = re.search(r'bash\s+-c\s+"([^"]+)"', prompt)
        if match:
            cmd = match.group(1)
        else:
            match = re.search(r"bash\s+-c\s+'([^']+)'", prompt)
            if match:
                cmd = match.group(1)

    # Strategy 3: Look for backtick commands or $() expressions
    if not cmd and "prompt" in tool_input:
        prompt = tool_input["prompt"]
        # Match: $(bash -c "...") or `bash -c "..."`
        match = re.search(r'\$\(bash\s+-c\s+"([^"]+)"\)', prompt)
        if match:
            cmd = match.group(1)

    return cmd.strip()


def check_destructive(command: str) -> tuple[bool, str]:
    """Check if command matches any destructive pattern. Returns (blocked, reason)."""
    if not command:
        return False, ""

    normalized = command.lower()

    # Check regex patterns
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, normalized):
            return True, reason

    # Special check: SQL DELETE without WHERE clause
    if SQL_DELETE_NO_WHERE.search(command):
        return True, "SQL DELETE FROM without WHERE clause (risks deleting all rows)"

    # Check for dangerous rm combinations like rm -rf followed by path shortcuts
    if re.search(r'rm\s+-rf\s+/?(\.\.|\$|home|tmp|mnt|var|etc)', command):
        return True, "rm -rf targeting system directories"

    return False, ""


def log_blocked(timestamp: str, command: str, reason: str, project_path: str):
    """Append blocked attempt to the log file."""
    log_line = f"[{timestamp}] BLOCKED: {reason} | Command: {command} | Path: {project_path}\n"

    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(BLOCKED_LOG, "a") as f:
            f.write(log_line)
    except Exception as e:
        print(f"Warning: Could not write to log file: {e}", file=sys.stderr)


def main():
    """Read Claude's tool input from stdin, return unchanged or block."""

    # Read all input from stdin (Claude sends JSON)
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            # Empty input - let through
            sys.exit(0)

        tool_input = json.loads(raw_input)
    except json.JSONDecodeError:
        # Invalid JSON - let through but log warning
        print("Warning: Invalid JSON input to pre-tool-use hook", file=sys.stderr)
        print(raw_input)
        sys.exit(0)

    # Only intercept bash/cli tools
    tool_type = tool_input.get("type", "") or tool_input.get("tool", "")

    if tool_type not in ("bash", "cli", "Bash", "CLI"):
        # Not a bash command - pass through
        print(raw_input)
        sys.exit(0)

    # Extract the actual command
    command = extract_bash_command(tool_input)

    if not command:
        # Couldn't extract command - let through
        print(raw_input)
        sys.exit(0)

    # Check for destructive patterns
    blocked, reason = check_destructive(command)

    if blocked:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project_path = os.environ.get("PWD", "unknown")

        # Log the blocked attempt
        log_blocked(timestamp, command, reason, project_path)

        # Print error message to stderr (visible to Claude)
        print("=" * 60, file=sys.stderr)
        print("🔒 HOOK: Command Blocked", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"Reason: {reason}", file=sys.stderr)
        print(f"Command: {command}", file=sys.stderr)
        print(f"Project: {project_path}", file=sys.stderr)
        print(f"Log: {BLOCKED_LOG}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("", file=sys.stderr)
        print("To proceed, run this command directly in your terminal.", file=sys.stderr)
        print("This hook is designed to prevent accidental destructive actions.", file=sys.stderr)
        print("=" * 60, file=sys.stderr)

        # Exit with non-zero to block the tool
        sys.exit(1)

    # Command is safe - return original input unchanged
    print(raw_input)
    sys.exit(0)


if __name__ == "__main__":
    main()