#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive commands.
Installed into ~/.claude/hooks/pre_tool_use/block.sh (symlinked from block.sh)
"""

import json
import os
import re
import sys
import time
from pathlib import Path

BLOCKED_ENTRIES = [
    # Each entry: (pattern, case_sensitive, reason)
    # case_sensitive=True means pattern is used as-is (for literal patterns)
    # case_sensitive=False means re.IGNORECASE is added

    (r"(?:^|\s)rm\s+-rf(?:$|\s)", True, "⚠️  'rm -rf' permanently deletes files. Use a targeted `rm` with explicit paths instead."),
    (r"(?:^|\s)rm\s+-fr(?:$|\s)", True, "⚠️  'rm -fr' permanently deletes files. Use a targeted `rm` with explicit paths instead."),
    (r"(?:^|\s)rm\s+-r\s+/\s*$", True, "⚠️  Recursive delete on root filesystem — will brick the system. Aborted."),
    (r"(?:^|\s)rm\s+-rf\s+/\s*$", True, "⚠️  Recursive force delete on root — will brick the system. Aborted."),
    (r"(?:^|\s)rm\s+-rf\s+--no-preserve-root", True, "⚠️  Explicit root deletion — will brick the system. Aborted."),
    (r"\bDROP\s+TABLE\b(?!\s+IF\s+EXISTS)", False, "⚠️  DROP TABLE without IF EXISTS is destructive. Add `IF EXISTS` before the table name."),
    (r"\bDROP\s+DATABASE\b(?!\s+IF\s+EXISTS)", False, "⚠️  DROP DATABASE destroys all data. Add `IF EXISTS` or use a migration script."),
    (r"\bTRUNCATE\b", False, "⚠️  TRUNCATE removes all rows irreversibly. Prefer DELETE with a WHERE clause or use a migration file."),
    (r"\bgit push --force$", True, "⚠️  `git push --force` overwrites remote history. Use `git push --force-with-lease` instead."),
    (r"\bgit push -f$", True, "⚠️  `git push -f` overwrites remote history. Use `git push --force-with-lease` instead."),
    ("> /dev/sd[a-z]", True, "⚠️  Direct disk write detected. This will corrupt block devices."),
    (r"\bmkfs\.\w", False, "⚠️  Filesystem formatting detected — will destroy all data on the target device."),
    (":(){ :|:& };:", True, "⚠️  Fork bomb detected. This will crash the system immediately."),
    ("chmod 000 /\s*$", True, "⚠️  Removing all permissions from root — will break the OS and require recovery mode."),
    ("chown -R 0:0 /\s*$", True, "⚠️  Recursive ownership change on root to root — dangerous when done without explicit target path."),
    ("mv /* /dev/null", True, "⚠️  Moving all files to /dev/null will permanently destroy the operating system."),
    (r"\bshred\s", False, "⚠️  `shred` overwrites and deletes files irreversibly. Use `rm` instead."),
    (r"\bdd\s+if=", False, "⚠️  `dd` with an `if=` source can overwrite raw devices. Verify the target is correct."),
    ("dd of=/dev/sd", True, "⚠️  `dd` output to a block device can destroy the disk and all partitions."),
]

# DELETE FROM is handled separately with WHERE-clause detection
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
HAS_WHERE_RE = re.compile(r"\bWHERE\b\s+\S", re.IGNORECASE)

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def has_delete_from_without_where(cmd: str) -> tuple[bool, str]:
    """Check if DELETE FROM appears without a WHERE clause."""
    if not DELETE_FROM_RE.search(cmd):
        return False, ""
    if HAS_WHERE_RE.search(cmd):
        return False, ""
    return True, "⚠️  DELETE FROM without a WHERE clause removes ALL rows. Add a WHERE clause to target specific rows."


def matches_blocked(command: str) -> tuple[bool, str]:
    for pattern, case_sensitive, reason in BLOCKED_ENTRIES:
        flags = 0 if case_sensitive else re.IGNORECASE
        if re.search(pattern, command, flags):
            return True, reason
    # Check DELETE FROM separately
    return has_delete_from_without_where(command)


def find_matched_pattern(command: str) -> str:
    """Find which pattern matched, for the error message."""
    for pattern, case_sensitive, _ in BLOCKED_ENTRIES:
        flags = 0 if case_sensitive else re.IGNORECASE
        if re.search(pattern, command, flags):
            return pattern
    return r"\bDELETE\s+FROM\b (no WHERE clause)"


def log_block(cmd: str, pattern: str, reason: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] BLOCKED: matched pattern '{pattern}'\n")
        f.write(f"  Command: {cmd[:200]}\n")
        f.write(f"  Reason:  {reason}\n")
        f.write(f"  Project: {os.getcwd()}\n")
        f.write("---\n")


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IndexError):
        # If we can't parse, let the command through (fail safe for hooks)
        print(json.dumps({"allowed": True}))
        return

    command_parts = payload.get("command", [])
    full_command = " ".join(command_parts)

    blocked, reason = matches_blocked(full_command)
    if blocked:
        pattern_matched = find_matched_pattern(full_command)
        log_block(full_command, pattern_matched, reason)
        result = {
            "allowed": False,
            "reason": (
                f"{reason}\n\n"
                f"  Pattern matched: `{pattern_matched}`\n"
                f"  Full command:    `{full_command[:250]}`\n\n"
                "To proceed anyway, disable the hook or write the command into a script file and run that."
            )
        }
        print(json.dumps(result))
        return

    print(json.dumps({"allowed": True}))


if __name__ == "__main__":
    main()
