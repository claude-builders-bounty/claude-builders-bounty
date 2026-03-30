#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook
Blocks dangerous commands before execution.

Install: Place in ~/.claude/hooks/ and add to settings.json:
  "hooks": {
    "pre-tool-use": [{"hook": "path/to/pre_tool_use_hook.py"}]
  }
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Dangerous command patterns — matched case-insensitively
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (r'rm\s+-rf\s+/\S+',                        "rm -rf on path — destructive deletion"),
    (r'rm\s+-rf\s+$',                           "rm -rf / — root filesystem deletion"),
    # Database destruction
    (r'DROP\s+(?:TABLE|DATABASE|MATERIALIZED)', "DROP — destructive database operation"),
    (r'TRUNCATE\s+TABLE',                       "TRUNCATE TABLE — destructive operation"),
    # Data deletion without safety
    (r'DELETE\s+FROM\s+(?:\w+\s*,\s*)*\w+(?:\s+(?!WHERE|LIMIT|ORDER|RETURNING|;))*', 
                                                           "DELETE without WHERE — data loss risk"),
    # Git history rewrite
    (r'git\s+push\s+--force(?=\s|--|$|-v)',    "git push --force — rewrites remote history"),
    (r'git\s+push\s+-f(?=\s|$)',                "git push -f — rewrites remote history"),
    # Dangerous network/file operations
    (r'chmod\s+777\s+/\S+',                     "chmod 777 on system path — security risk"),
    (r'mkfs\.',                                 "mkfs — filesystem format, destructive"),
    (r'dd\s+if=.*of=/dev/',                     "dd to block device — potentially destructive"),
    # Shell escapes
    (r':!\s*rm\s+-rf',                          "vim :!rm -rf — shell escape"),
    (r'%\s*rm\s+-rf',                           "IPython/Perl !rm -rf — shell escape"),
]

DANGEROUS_PATTERNS = [(re.compile(p, re.IGNORECASE), m) for p, m in DANGEROUS_PATTERNS]

# Paths that are considered sensitive (read or write = blocked)
SENSITIVE_PATHS = [
    '/etc/shadow', '/etc/passwd', '/etc/sudoers',
    '/etc/ssh/', '/root/.ssh/', '/home/*/.ssh/',
    '~/.ssh/', '/.ssh/',
    '~/.aws/', '/.aws/',
    '~/.gnupg/', '/.gnupg/',
]

def is_sensitive_path(path: str) -> bool:
    path = os.path.normpath(os.path.expanduser(path))
    for sensitive in SENSITIVE_PATHS:
        sensitive = os.path.normpath(os.path.expanduser(sensitive))
        if path.startswith(sensitive) or path == sensitive:
            return True
    return False

def check_command(command_str: str) -> tuple[bool, str | None]:
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command_str):
            return True, reason
    return False, None

def log_blocked(tool_name: str, command: str, reason: str, project_path: str):
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    with open(BLOCKED_LOG, "a") as f:
        f.write(
            f"[{datetime.now().isoformat()}] "
            f"BLOCKED {tool_name} in {project_path}\n"
            f"  Reason: {reason}\n"
            f"  Command: {command}\n\n"
        )

def build_blocked_message(tool_name: str, command: str, reason: str) -> str:
    return (
        f"\n{'='*60}\n"
        f"HOOK BLOCKED: {tool_name}\n"
        f"{'='*60}\n"
        f"Reason: {reason}\n\n"
        f"Command:\n  {command}\n\n"
        f"This command was blocked by your pre-tool-use hook.\n"
        f"If you believe this is a false positive, you can:\n"
        f"  1. Modify the command to be safer\n"
        f"  2. Temporarily disable the hook: remove from settings.json\n"
        f"  3. Ask your human for confirmation before proceeding\n\n"
        f"Full log: {BLOCKED_LOG}\n"
        f"{'='*60}\n"
    )

def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = payload.get("name", payload.get("tool", "unknown"))
    tool_input = payload.get("toolInput", {})

    # Read operations: block sensitive file access
    if tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if is_sensitive_path(file_path):
            reason = f"Reading sensitive path: {file_path}"
            log_blocked(tool_name, file_path, reason, os.environ.get("CLAUDE_PROJECT_PATH", "."))
            print(build_blocked_message(tool_name, file_path, reason), file=sys.stderr)
            sys.exit(1)

    # Write/Edit operations: block sensitive file writes
    if tool_name in ("Write", "Edit", "MultiEdit"):
        file_path = tool_input.get("path", "")
        if is_sensitive_path(file_path):
            reason = f"Writing to sensitive path: {file_path}"
            log_blocked(tool_name, file_path, reason, os.environ.get("CLAUDE_PROJECT_PATH", "."))
            print(build_blocked_message(tool_name, file_path, reason), file=sys.stderr)
            sys.exit(1)

    # Bash: check dangerous commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if not command:
            sys.exit(0)

        blocked, reason = check_command(command)
        if blocked:
            log_blocked(tool_name, command, reason, os.environ.get("CLAUDE_PROJECT_PATH", "."))
            print(build_blocked_message(tool_name, command, reason), file=sys.stderr)
            sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
