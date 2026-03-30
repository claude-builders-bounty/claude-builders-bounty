#!/usr/bin/env python3
"""
Pre-tool-use hook: blocks destructive bash commands
Claude Code hooks format: https://docs.anthropic.com/claude-code/hooks

Usage:
  In Claude Code settings.json, add:
  {
    "hooks": {
      "pre-tool-use": "python3 /path/to/pre_tool_hook.py"
    }
  }
"""

import sys
import os
import re
from datetime import datetime
from pathlib import Path

BLOCKED_PATTERNS = [
    re.compile(r'rm\s+-rf\s+/', re.IGNORECASE),
    re.compile(r'rm\s+-rf\s+~', re.IGNORECASE),
    re.compile(r'rm\s+-rf\s+--', re.IGNORECASE),
    re.compile(r'DROP\s+TABLE', re.IGNORECASE),
    re.compile(r'TRUNCATE\s+TABLE', re.IGNORECASE),
    re.compile(r'DELETE\s+FROM\s+\w+\s*;?\s*$', re.IGNORECASE),
    re.compile(r'git\s+push\s+--force', re.IGNORECASE),
    re.compile(r'git\s+push\s+-f', re.IGNORECASE),
    re.compile(r'ALTER\s+TABLE.*DROP', re.IGNORECASE),
    re.compile(r'sudo\s+rm', re.IGNORECASE),
    re.compile(r'chmod\s+-R\s+777\s+/', re.IGNORECASE),
    re.compile(r'mkfs', re.IGNORECASE),
    re.compile(r':\(\s*:\||&\s*;\s*\):', re.IGNORECASE),
    re.compile(r'dd\s+if=/dev/zero\s+of=/dev/', re.IGNORECASE),
    re.compile(r'(wget|curl).*\|\s*sh', re.IGNORECASE),
]

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
PROJECT_PATH = os.environ.get("PROJECT_DIR", os.getcwd())


def is_blocked(command: str) -> tuple[bool, str]:
    """Check if command matches any blocked pattern."""
    for pattern in BLOCKED_PATTERNS:
        if pattern.search(command):
            return True, pattern.pattern
    return False, ""


def log_blocked(command: str, reason: str):
    """Log blocked command to file."""
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED: {command} | Reason: {reason} | Project: {PROJECT_PATH}\n")


def print_blocked_message(command: str, reason: str):
    """Print user-friendly blocked message."""
    print()
    print("=" * 50)
    print("HOOK: COMMAND BLOCKED")
    print("=" * 50)
    print()
    print("This command was blocked by the safety hook:")
    print()
    print(f"  {command}")
    print()
    print(f"Reason: Matches blocked pattern: {reason}")
    print()
    print("If this is a legitimate command:")
    print("  1. Ask the user to confirm the action")
    print("  2. Run outside Claude Code with proper safeguards")
    print()
    print(f"Logged to: {BLOCKED_LOG}")
    print("=" * 50)
    print()


def main():
    """Main hook function."""
    args = sys.argv[1:]
    
    if len(args) < 2:
        sys.exit(0)  # Allow unknown tool calls
    
    tool_name = args[0]
    tool_input = " ".join(args[1:])
    
    # Only check Bash tool
    if tool_name != "Bash":
        sys.exit(0)
    
    blocked, reason = is_blocked(tool_input)
    
    if blocked:
        log_blocked(tool_input, reason)
        print_blocked_message(tool_input, reason)
        sys.exit(1)  # Block the command
    
    sys.exit(0)  # Allow the command


if __name__ == "__main__":
    main()
