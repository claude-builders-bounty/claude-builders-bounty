#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code
Blocks destructive bash commands before execution.

Install:
  mkdir -p ~/.claude/hooks/
  cp block_destructive.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/block_destructive.py

Claude Code will detect and run this hook automatically.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that are ALWAYS blocked
DESTRUCTIVE_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+/home",
    r"rm\s+-rf\s+/root",
    r"rm\s+-rf\s+/etc",
    r"rm\s+-rf\s+/var",
    r"rm\s+-rf\s+/usr",
    r"mkfs",
    r"dd\s+if=.*of=",
    r":(){ :|:& };:",  # Fork bomb
]

# Patterns blocked in SQL contexts
SQL_DESTRUCTIVE_PATTERNS = [
    r"DROP\s+DATABASE",
    r"DROP\s+TABLE",
    r"DROP\s+SCHEMA",
    r"TRUNCATE\s+(?!\()",
    r"DELETE\s+FROM\s+\w+\s+(?!WHERE)",
    r"ALTER\s+TABLE.*DROP",
]

# Patterns blocked in git contexts
GIT_DESTRUCTIVE_PATTERNS = [
    r"git\s+push\s+--force",
    r"git\s+push\s+-f",
    r"git\s+reset\s+--hard",
    r"git\s+rebase\s+--interactive",
    r"git\s+clean\s+-f[df]",
    r"git\s+filter-branch",
]

# Patterns blocked for filesystem safety
FS_DESTRUCTIVE_PATTERNS = [
    r"chmod\s+-R\s+0",
    r"chown\s+-R.*:\s*/",
    r">\s*/dev/(sda|sdb|sdc|nvme|mmcblk)",
    r"pv|/dev/(sda|sdb|sdc)",
    r"shutdown\s+-h\s+now",
    r"reboot",
    r"init\s+0",
    r"poweroff",
]

ALL_PATTERNS = {
    "destructive": DESTRUCTIVE_PATTERNS,
    "sql": SQL_DESTRUCTIVE_PATTERNS,
    "git": GIT_DESTRUCTIVE_PATTERNS,
    "filesystem": FS_DESTRUCTIVE_PATTERNS,
}


def log_blocked(category: str, command: str, project_path: str):
    """Log a blocked command attempt."""
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "category": category,
        "command": command,
        "project_path": project_path,
    }
    with open(BLOCKED_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def should_block(command: str) -> tuple[bool, str, str]:
    """
    Check if a command should be blocked.
    Returns (block, category, reason).
    """
    command_lower = command.lower()
    project_path = os.getcwd()

    for category, patterns in ALL_PATTERNS.items():
        import re
        for pattern in patterns:
            if re.search(pattern, command_lower):
                return True, category, f"Matched pattern: {pattern}"

    return False, "", ""


def main():
    """Main hook entry point."""
    # Read the command from stdin (Claude Code passes it as JSON)
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IndexError):
        # Cannot parse input; allow the command to proceed
        print(json.dumps({"allow": True}))
        return

    command = input_data.get("cmd", input_data.get("command", ""))
    if not command:
        print(json.dumps({"allow": True}))
        return

    block, category, reason = should_block(command)
    if block:
        project_path = os.getcwd()
        log_blocked(category, command, project_path)
        print(json.dumps({
            "allow": False,
            "reason": (
                f"⚠️ 命令已被安全钩子拦截\n"
                f"  分类: {category}\n"
                f"  命令: {command[:200]}\n"
                f"  原因: 该操作可能对系统或仓库造成不可逆的破坏。\n"
                f"  如需执行，请在Claude Code中手动确认。"
            ),
        }))
        return

    print(json.dumps({"allow": True}))


if __name__ == "__main__":
    main()
