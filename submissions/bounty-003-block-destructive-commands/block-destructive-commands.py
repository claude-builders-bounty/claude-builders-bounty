#!/usr/bin/env python3
"""
Claude Code Hook: Block Destructive Bash Commands
==================================================

A PreToolUse hook for Claude Code that intercepts and blocks destructive
bash commands before they execute. Provides a configurable allowlist,
detailed logging, and clear explanations for every blocked command.

Installation (2 commands):
  1. cp block-destructive-commands.py ~/.claude/hooks/
  2. Add the hook config to ~/.claude/settings.json (see README.md)

Read more about hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Default blocklist: regex pattern -> reason message
# The hook checks each pattern against the full command string.
DESTRUCTIVE_PATTERNS: list[tuple[str, str]] = [
    # --- Filesystem destruction ---
    (r"\brm\s+-rf\b", "Recursive force delete (rm -rf). Use with extreme caution."),
    (r"\brm\s+-r\s+-f\b", "Recursive force delete (rm -r -f). Use with extreme caution."),
    (r"\brm\s+--recursive\s+--force\b", "Recursive force delete (rm --recursive --force)."),
    (r"\brm\s+-rf\s+/\b", "rm -rf / — would delete the entire filesystem!"),
    (r"\brm\s+-rf\s+/[a-zA-Z]", "rm -rf on a system directory — high risk of data loss."),

    # --- Disk/block device destruction ---
    (r"\bdd\b", "dd — can overwrite disks and partitions. Use only if you are certain."),
    (r"\bdd\s+if=.*\s+of=/dev/", "dd writing directly to a block device — can destroy data."),
    (r"\bmkfs\b", "mkfs — formats a filesystem, destroying all data on it."),
    (r"\bmkfs\.ext[234]\b", "mkfs.ext* — formats an ext filesystem, destroying all data."),
    (r"\bmkfs\.btrfs\b", "mkfs.btrfs — creates a Btrfs filesystem, erasing existing data."),
    (r"\bmkfs\.xfs\b", "mkfs.xfs — creates an XFS filesystem, erasing existing data."),
    (r"\bmkfs\.fat\b", "mkfs.fat — creates a FAT filesystem, erasing existing data."),
    (r"\bformat\b", "format command — can erase disks and partitions."),
    (r"\bfdisk\b", "fdisk — partition editor that can destroy partition tables."),
    (r"\bparted\b", "parted — partition editor that can destroy partition tables."),
    (r"\bmkswap\b", "mkswap — sets up a swap area, potentially overwriting data."),
    (r"\bwipefs\b", "wipefs — wipes filesystem signatures from a device."),
    (r"\bshred\b", "shred — securely deletes files by overwriting them."),

    # --- Shell redirect to block devices ---
    (r">\s*/dev/sd[a-z]", "Shell redirect to a block device — can destroy disk data."),
    (r">\s*/dev/nvme", "Shell redirect to a block device — can destroy disk data."),
    (r">\s*/dev/mmcblk", "Shell redirect to a block device — can destroy disk data."),

    # --- Permission abuse ---
    (r"chmod\s+-R\s+777\b", "chmod -R 777 — opens all permissions recursively. Security risk."),
    (r"chmod\s+777\s+-R\b", "chmod 777 -R — opens all permissions recursively. Security risk."),
    (r"chmod\s+--recursive\s+777\b", "chmod --recursive 777 — security risk."),
    (r"chown\s+-R\b", "chown -R — recursive ownership change. Can break system permissions."),

    # --- Fork bomb ---
    (r":\(\s*\)\s*\{", "Fork bomb detected (:(){...}) — would crash the system."),

    # --- Moving root/system directories ---
    (r"\bmv\s+/\s+", "mv / — moving the root directory would break the system."),
    (r"\bmv\s+/[a-zA-Z]+\s+/dev/null", "Moving a directory to /dev/null — data loss."),

    # --- System commands ---
    (r"\breboot\b", "reboot — restarts the system."),
    (r"\bshutdown\b", "shutdown — shuts down or reboots the system."),
    (r"\bhalt\b", "halt — stops the system."),
    (r"\bpoweroff\b", "poweroff — powers off the system."),
    (r"\binit\s+0\b", "init 0 — shuts down the system."),
    (r"\binit\s+6\b", "init 6 — reboots the system."),

    # --- Sudo with dangerous commands ---
    (r"\bsudo\s+rm\b", "sudo rm — running rm with elevated privileges."),
    (r"\bsudo\s+dd\b", "sudo dd — running dd with elevated privileges."),

    # --- Database destruction ---
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE — would delete an entire database."),
    (r"\bDROP\s+TABLE\b", "DROP TABLE — would delete a database table."),
    (r"\bTRUNCATE\b", "TRUNCATE — removes all rows from a database table."),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause — would delete all rows."),

    # --- Git force push ---
    (r"\bgit\s+push\s+--force\b", "git push --force — force-pushes, overwriting remote history."),
    (r"\bgit\s+push\s+-f\b", "git push -f — force-pushes, overwriting remote history."),
    (r"\bgit\s+push\s+--force-with-lease\b", "git push --force-with-lease — force-pushes (safer, but still destructive)."),

    # --- Pip install without review ---
    (r"\bcurl\s+.*\|\s*bash\b", "curl | bash — downloads and executes a script directly."),
    (r"\bwget\s+.*\|\s*bash\b", "wget | bash — downloads and executes a script directly."),
    (r"\bcurl\s+.*\|\s*sh\b", "curl | sh — downloads and executes a script directly."),
    (r"\bwget\s+.*\|\s*sh\b", "wget | sh — downloads and executes a script directly."),

    # --- Dangerous flag combinations ---
    (r"\brm\s+-rf\s+--no-preserve-root\b", "rm -rf --no-preserve-root — disables root protection."),
]

# Configurable allowlist: patterns that make a destructive command safe
# These are checked AFTER the blocklist match. If any allowlist pattern
# matches the command, it will be ALLOWED (not blocked).
# Patterns are regex. Common use: allow rm -rf in node_modules, .next, etc.
ALLOWLIST_PATTERNS: list[str] = [
    # Safe recursive deletes in dependency directories
    r"rm\s+-rf\s+(\./)?node_modules",
    r"rm\s+-rf\s+(\./)?\.next",
    r"rm\s+-rf\s+(\./)?build",
    r"rm\s+-rf\s+(\./)?dist",
    r"rm\s+-rf\s+(\./)?\.venv",
    r"rm\s+-rf\s+(\./)?__pycache__",
    r"rm\s+-rf\s+(\./)?\.git/.*\.lock",
    # Safe use of dd for making bootable USB (if explicitly targeting a non-system path)
    r"dd\s+if=.*\.iso\s+of=/dev/sd[a-z]$",  # Only match if it's just iso -> device
    # rm -rf with temp directories
    r"rm\s+-rf\s+/tmp/",
    r"rm\s+-rf\s+/var/tmp/",
]

# Log file location
LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def load_allowlist() -> list[str]:
    """
    Load user-customized allowlist from ~/.claude/hooks/allowlist.txt if it exists.
    The file should contain one regex pattern per line. Empty lines and lines
    starting with # are ignored.
    """
    allowlist_path = LOG_DIR / "allowlist.txt"
    patterns: list[str] = []
    if allowlist_path.exists():
        try:
            with open(allowlist_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
        except OSError:
            pass  # If we can't read it, just use defaults
    return patterns


def is_command_destructive(command: str) -> tuple[bool, str]:
    """
    Check if a command matches any destructive pattern.
    Returns (is_destructive, reason).
    """
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check allowlist
            if is_command_allowed(command):
                return False, ""
            return True, reason
    return False, ""


def is_command_allowed(command: str) -> bool:
    """
    Check if a command matches any allowlist pattern.
    """
    all_patterns = list(ALLOWLIST_PATTERNS)
    all_patterns.extend(load_allowlist())

    for pattern in all_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def log_blocked(command: str, reason: str, project_path: str) -> None:
    """
    Log a blocked command attempt to the log file.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "command": command,
            "reason": reason,
            "project_path": project_path,
        }
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except OSError:
        pass  # Silently fail if we can't write the log


def get_project_path() -> str:
    """Get the current project path from environment or cwd."""
    for env_var in ["CLAUDE_PROJECT_DIR", "PWD"]:
        val = os.environ.get(env_var)
        if val:
            return val
    return os.getcwd()


def main() -> None:
    # Read JSON input from stdin (provided by Claude Code)
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error parsing hook input: {e}", file=sys.stderr)
        sys.exit(1)

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Bash" and tool_name != "Terminal":
        # Not a bash tool call — let it through
        sys.exit(0)

    tool_input = input_data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check if the command is destructive
    is_destructive, reason = is_command_destructive(command)
    if not is_destructive:
        sys.exit(0)

    # Log the blocked attempt
    project_path = get_project_path()
    log_blocked(command, reason, project_path)

    # Print the reason to stderr (shown to user)
    print(
        f"⛔ BLOCKED: Destructive command detected.\n"
        f"  Command: {command[:200]}{'...' if len(command) > 200 else ''}\n"
        f"  Reason:  {reason}\n"
        f"  Logged:  {LOG_FILE}\n\n"
        f"If you need to run this command:\n"
        f"  1. Add an allowlist pattern to {LOG_DIR / 'allowlist.txt'}\n"
        f"  2. Or run the command manually outside Claude Code",
        file=sys.stderr,
    )

    # Use the standard hook API to deny the tool call
    # This returns a JSON decision on stdout that Claude Code processes
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Destructive command blocked by hook.\n"
                f"Command: {command[:200]}{'...' if len(command) > 200 else ''}\n"
                f"Reason: {reason}"
            ),
        }
    }
    print(json.dumps(decision))
    sys.exit(0)


if __name__ == "__main__":
    main()
