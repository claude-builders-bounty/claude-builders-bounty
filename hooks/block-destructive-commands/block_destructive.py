#!/usr/bin/env python3
"""
PreToolUse Hook: Destructive Command Interceptor for Claude Code
Blocks dangerous shell commands, logs blocked attempts, and passes safe commands.
Follows Anthropic Claude Code hook specifications.
Exit code 0: Command allowed
Exit code 2: Command blocked (stderr fed back to Claude)
"""

import sys
import json
import re
import os
from datetime import datetime
from pathlib import Path

# Configurable patterns
BLOCKED_PATTERNS = [
    # 1. Recursive forceful deletion
    (
        r"(?:^|[\s;&|`\$\(\)])(?:sudo\s+)?rm\s+(?:-[a-zA-Z0-9]*[rf][a-zA-Z0-9]*\s+|--recursive\s+|--force\s+)*-[a-zA-Z0-9]*[rf]",
        "rm with recursive/force flags (-r, -f, --recursive, --force)"
    ),
    (
        r"(?:^|[\s;&|`\$\(\)])(?:sudo\s+)?rm\s+(?:-[a-zA-Z0-9]+\s+)*(--recursive|--force)",
        "rm with long-form recursive/force options"
    ),
    # 2. Dangerous SQL statements
    (
        r"(?i)\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW)\b",
        "Destructive SQL DROP statement"
    ),
    (
        r"(?i)\bTRUNCATE(?:\s+TABLE)?\b",
        "Destructive SQL TRUNCATE statement"
    ),
    (
        r"(?i)\bDELETE\s+FROM\s+[\w\.\"`']+\s*(?:;\s*$|$|\)(?!\s*WHERE)|(?<!\bWHERE\b)(?:;\s*|&&|\|\|))",
        "SQL DELETE FROM statement without a WHERE clause"
    ),
    # 3. Dangerous Git operations
    (
        r"(?:^|[\s;&|`\$\(\)])git\s+push\s+(?:[^\n;&|]*\s+)?(?:-f\b|--force\b|--force-with-lease\b)",
        "Git force push operation (-f, --force, --force-with-lease)"
    ),
    # 4. Critical system destruction
    (
        r"(?:^|[\s;&|`\$\(\)])(?:sudo\s+)?mkfs(?:\.[a-zA-Z0-9]+)?\b",
        "Filesystem formatting utility (mkfs)"
    ),
    (
        r"(?:^|[\s;&|`\$\(\)])(?:sudo\s+)?dd\s+if=.*of=/dev/(?:sd[a-z]|nvme|vd[a-z]|disk)",
        "Raw block device overwrite via dd"
    ),
]

def check_delete_without_where(cmd: str) -> bool:
    """Specialized validator for DELETE FROM to ensure a valid WHERE clause is present."""
    pattern = re.compile(r"(?i)\bDELETE\s+FROM\s+([a-zA-Z0-9_\"`\.]+)(.*)", re.DOTALL)
    match = pattern.search(cmd)
    if not match:
        return False
    after_clause = match.group(2)
    # Check if WHERE exists before any statement terminator or end of string
    # Split by semicolon to inspect the specific DELETE statement
    statement_chunk = re.split(r"[;&|]", after_clause)[0]
    return not bool(re.search(r"(?i)\bWHERE\b", statement_chunk))

def inspect_command(cmd: str):
    """
    Evaluates a command string against blocked patterns.
    Returns (is_blocked: bool, reason: str).
    """
    if not cmd or not isinstance(cmd, str):
        return False, ""

    # Check DELETE without WHERE explicitly
    if check_delete_without_where(cmd):
        return True, "SQL DELETE FROM statement without a WHERE clause"

    for pattern, desc in BLOCKED_PATTERNS:
        if re.search(pattern, cmd):
            return True, desc

    return False, ""

def log_blocked(cmd: str, reason: str, project_dir: str):
    """Logs blocked attempts to ~/.claude/hooks/blocked.log with timestamp and project path."""
    home_dir = Path(os.environ.get("HOME", str(Path.home())))
    claude_hooks_dir = home_dir / ".claude" / "hooks"
    claude_hooks_dir.mkdir(parents=True, exist_ok=True)
    log_file = claude_hooks_dir / "blocked.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = (
        f"[{timestamp}] BLOCKED: {reason}\n"
        f"  Command: {cmd.strip()}\n"
        f"  Project: {project_dir}\n"
        f"{'-' * 60}\n"
    )

    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def main():
    # Read payload from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.exit(0)
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        # If payload is raw text or unrecognized format, assume safe or pass through
        sys.exit(0)
    except Exception:
        sys.exit(0)

    # Determine command content based on Claude Code tool calling convention
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    
    # Only inspect Bash or shell tools
    if tool_name and tool_name.lower() not in ("bash", "shell", "terminal"):
        sys.exit(0)

    cmd = ""
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command", "") or tool_input.get("cmd", "")
    elif isinstance(tool_input, str):
        cmd = tool_input

    # Also support direct payload where data has 'command'
    if not cmd and "command" in data:
        cmd = data["command"]

    if not cmd:
        sys.exit(0)

    is_blocked, reason = inspect_command(cmd)

    if is_blocked:
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        log_blocked(cmd, reason, project_dir)

        # Stderr is passed back to Claude to explain the refusal
        error_msg = (
            f"\n[SECURITY GUARD] Command Execution Blocked!\n"
            f"Pattern Detected : {reason}\n"
            f"Blocked Command  : {cmd}\n"
            f"Audit Logging    : Recorded in ~/.claude/hooks/blocked.log\n"
            f"Reason           : Destructive operations (rm -rf, git push --force, DROP TABLE, "
            f"TRUNCATE, unconstrained DELETE) are strictly prohibited by safety policy.\n"
            f"Action Required  : Reformulate the command safely without destructive operations.\n"
        )
        sys.stderr.write(error_msg)
        # Exit code 2 instructs Claude Code to abort the tool execution and deliver stderr
        sys.exit(2)

    # Allowed
    sys.exit(0)

if __name__ == "__main__":
    main()
