#!/usr/bin/env python3
"""
pre_tool_use_hook.py — Claude Code Pre-Tool-Use Hook (Python Version)

Intercepts and blocks dangerous bash commands before execution.
Follows Claude Code hooks format: ~/.claude/hooks/

Installation:
    mkdir -p ~/.claude/hooks
    cp pre_tool_use_hook.py ~/.claude/hooks/pre-tool-use-hook
    chmod +x ~/.claude/hooks/pre-tool-use-hook
"""

import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────
HOME = Path.home()
LOG_FILE = HOME / ".claude" / "hooks" / "blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Dangerous patterns ───────────────────────────────────────────────────────
DANGEROUS_PATTERNS = [
    # Destructive file operations
    (r'rm\s+-rf', 'Destructive: rm -rf'),
    (r'rm\s+-fr', 'Destructive: rm -fr'),
    (r'rmdir\s+-f', 'Destructive: rmdir -f'),
    (r'mv.*/dev/null', 'Destructive: move to /dev/null'),
    (r'>\s*&&\s*rm', 'Destructive: redirect then rm'),
    (r'^:\s*>', 'Destructive: truncate file (:)'),
    (r'^>\s*\w', 'Destructive: truncate file (>)'),

    # Database destruction
    (r'DROP\s+TABLE', 'Destructive: DROP TABLE'),
    (r'DROP\s+DATABASE', 'Destructive: DROP DATABASE'),
    (r'TRUNCATE\s+TABLE', 'Destructive: TRUNCATE TABLE'),
    (r'TRUNCATE\s+\w+', 'Destructive: TRUNCATE'),
    (r'DELETE\s+FROM\s+\w+\s*$', 'Destructive: DELETE FROM without WHERE'),
    (r'DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*0', 'Destructive: DELETE WHERE 1=0'),
    (r'DELETE\s+FROM\s+\w+\s+WHERE\s+TRUE', 'Destructive: DELETE WHERE TRUE'),

    # Git destruction
    (r'git\s+push\s+--force', 'Destructive: git push --force'),
    (r'git\s+push\s+-f\b', 'Destructive: git push -f'),
    (r'git\s+reset\s+--hard', 'Destructive: git reset --hard'),
    (r'git\s+clean\s+-fdx', 'Destructive: git clean -fdx'),
    (r'git\s+clean\s+-dfx', 'Destructive: git clean -dfx'),

    # Shell destruction
    (r'exec\s+>\s*/', 'Destructive: exec redirect to root'),
    (r'exec\s+>&-', 'Destructive: exec close stdout'),
    (r'exec\s+<\s*/', 'Destructive: exec redirect from root'),

    # System destruction
    (r'\bmkfs\b', 'Destructive: mkfs (format disk)'),
    (r'dd\s+if=.*of=/dev/', 'Destructive: dd to /dev/'),
    (r'\bfdisk\b', 'Destructive: fdisk'),
    (r'\bparted\b', 'Destructive: parted'),
    (r'\bshutdown\b', 'Destructive: shutdown'),
    (r'\breboot\b', 'Destructive: reboot'),
    (r'\bpoweroff\b', 'Destructive: poweroff'),
    (r'\brmmod\b', 'Destructive: rmmod'),
    (r'\binsmod\b', 'Destructive: insmod'),
    (r'\bmodprobe\b', 'Destructive: modprobe'),

    # Package destruction
    (r'apt-get\s+remove', 'Destructive: apt-get remove'),
    (r'apt-get\s+purge', 'Destructive: apt-get purge'),
    (r'apt-get\s+autoremove', 'Destructive: apt-get autoremove'),
    (r'\byum\s+remove\b', 'Destructive: yum remove'),
    (r'\bdnf\s+remove\b', 'Destructive: dnf remove'),
    (r'\bbrew\s+uninstall\b', 'Destructive: brew uninstall'),
    (r'\bpip\s+uninstall\b', 'Destructive: pip uninstall'),
    (r'\bnpm\s+uninstall\b', 'Destructive: npm uninstall'),
]

COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), desc) for p, desc in DANGEROUS_PATTERNS]


def check_command(command_line):
    # type: (str) -> tuple
    """Check if a command matches any dangerous pattern."""
    for pattern, description in COMPILED_PATTERNS:
        if pattern.search(command_line):
            return (True, description)
    return (False, "")


def log_blocked(command_line, matched_desc):
    # type: (str, str) -> None
    """Log a blocked command attempt."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_path = os.getcwd()
    log_entry = "[{}] BLOCKED | Pattern: {} | Command: {} | Path: {}\n".format(
        timestamp, matched_desc, command_line, project_path
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)


def format_block_message(command_line, matched_desc):
    # type: (str, str) -> str
    """Format the block message for Claude."""
    return """🚫 **Command Blocked by Pre-Tool-Use Hook**

The following command was blocked because it matches a dangerous pattern:

```
{}
```

**Matched pattern:** `{}`

This command could cause irreversible damage:
- Data loss (rm -rf, DROP TABLE, TRUNCATE)
- Force push to remote (git push --force)
- System destruction (mkfs, dd to /dev/)
- Package removal (apt remove, pip uninstall)

**What to do:**
1. Review the command carefully
2. If you meant to run it, use the `--force` flag to bypass the hook
3. Consider safer alternatives (e.g., `rm -i` for interactive deletion)

""".format(command_line, matched_desc)


def main():
    # Read command from arguments or stdin
    if len(sys.argv) > 1:
        command_line = " ".join(sys.argv[1:])
    else:
        try:
            command_line = sys.stdin.read().strip()
        except Exception:
            command_line = ""

    if not command_line:
        sys.exit(0)

    # Check against patterns
    is_blocked, matched_desc = check_command(command_line)

    if is_blocked:
        log_blocked(command_line, matched_desc)
        sys.stderr.write(format_block_message(command_line, matched_desc))
        sys.exit(1)

    # Command is safe
    sys.exit(0)


if __name__ == "__main__":
    main()
