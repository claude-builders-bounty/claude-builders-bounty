#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Reads JSON event data from stdin, parses the bash command, and denies
execution if the command matches known destructive patterns.

Configuration (~/.claude/settings.json):
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre_tool_use_bash_guard.py"
          }
        ]
      }
    ]
  }
}

Input (stdin JSON):
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /"
  }
}

Output (stdout JSON on deny, empty on allow):
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "Blocked: recursive deletion of root directory"
}

Exit codes:
  0 — allow (command is safe or not a Bash command)
  1 — deny (command matched a destructive pattern)
"""
from __future__ import annotations

import json
import re
import sys
from typing import Any

# ──────────────────────────────────────────────────────────────────── #
# Destructive command patterns
# ──────────────────────────────────────────────────────────────────── #

# Each entry: (pattern, description, category)
# Patterns are compiled regexes matched against the full command string.
DESTRUCTIVE_PATTERNS: list[tuple[str, str, str]] = [
    # ── Recursive deletion ──
    (
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(/\s*$|/\s+|--no-preserve-root|/\*|/~/|/$)",
        "Recursive deletion of root or filesystem root",
        "recursive_delete",
    ),
    (
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+(/home|/etc|/usr|/var|/bin|/sbin|/boot|/dev|/proc|/sys|/lib|/opt|/root|/tmp)\s*$",
        "Recursive deletion of critical system directory",
        "recursive_delete",
    ),
    (
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+~\s*$",
        "Recursive deletion of home directory",
        "recursive_delete",
    ),
    (
        r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f?|-[a-zA-Z]*f[a-zA-Z]*r?)\s+\*\s*$",
        "Recursive deletion of all files in current directory",
        "recursive_delete",
    ),

    # ── Disk formatting ──
    (
        r"mkfs\.\w+\s+/dev/",
        "Disk formatting on block device",
        "disk_format",
    ),
    (
        r"mkfs\s+/dev/",
        "Disk formatting on block device",
        "disk_format",
    ),

    # ── Raw disk writes ──
    (
        r"dd\s+.*if=/dev/(zero|random|urandom).*of=/dev/",
        "Writing zeros/random data to block device",
        "disk_write",
    ),
    (
        r"dd\s+.*of=/dev/(sd|nvme|hd|vd|xvd)",
        "Writing directly to block device",
        "disk_write",
    ),

    # ── Fork bomb ──
    (
        r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;?\s*:",
        "Fork bomb detected",
        "fork_bomb",
    ),
    (
        r":\(\)\s*\{\s*:\|:\s*&\s*\}\s*;?\s*: &",
        "Fork bomb detected",
        "fork_bomb",
    ),

    # ── Permission escalation to world-writable ──
    (
        r"chmod\s+(-R\s+)?777\s+(/\s*$|/etc|/usr|/var|/bin|/sbin|/boot|/root|/home)",
        "Setting world-writable permissions on system directory",
        "permission_escalation",
    ),
    (
        r"chmod\s+(-R\s+)?000\s+/\s*$",
        "Removing all permissions from root directory",
        "permission_escalation",
    ),

    # ── Piping to shell execution ──
    (
        r"curl\s+.*\|\s*(sh|bash|zsh|fish)\b",
        "Piping remote content to shell execution",
        "remote_exec",
    ),
    (
        r"wget\s+.*\|\s*(sh|bash|zsh|fish)\b",
        "Piping remote content to shell execution",
        "remote_exec",
    ),

    # ── Obfuscated execution (base64 decode to shell) ──
    (
        r"echo\s+[A-Za-z0-9+/=]{20,}\s*\|\s*(base64\s+--?decode|base64\s+-d)\s*\|\s*(sh|bash|zsh|fish)\b",
        "Base64-decoded content piped to shell execution",
        "obfuscated_exec",
    ),
    (
        r"echo\s+[A-Za-z0-9+/=]{20,}\s*\|\s*base64\s+-d\s*\|\s*(sh|bash)\b",
        "Base64-decoded content piped to shell execution",
        "obfuscated_exec",
    ),

    # ── History/credential manipulation ──
    (
        r"cat\s+/dev/null\s*>\s*~/\.bash_history",
        "Clearing bash history",
        "history_clear",
    ),
    (
        r"cat\s+/dev/null\s*>\s*~/\.zsh_history",
        "Clearing zsh history",
        "history_clear",
    ),
    (
        r"rm\s+-f?\s*~/\.bash_history",
        "Removing bash history file",
        "history_clear",
    ),
    (
        r"unset\s+HISTFILE\s*;\s*unset\s+HISTSIZE",
        "Disabling shell history recording",
        "history_clear",
    ),

    # ── Kernel module manipulation ──
    (
        r"rmmod\s+-[a-zA-Z]*a[a-zA-Z]*",
        "Removing all kernel modules",
        "kernel_manipulation",
    ),
    (
        r"sysctl\s+-w\s+kernel\.\w+=0",
        "Disabling kernel security parameter",
        "kernel_manipulation",
    ),

    # ── Force kill all processes ──
    (
        r"killall\s+-9\s+\*",
        "Force killing all processes",
        "process_kill",
    ),
    (
        r"kill\s+-9\s+-1\b",
        "Sending SIGKILL to all processes (PID -1)",
        "process_kill",
    ),

    # ── Shutdown/reboot ──
    (
        r"\b(shutdown|poweroff|halt|reboot)\s+",
        "System shutdown or reboot command",
        "shutdown",
    ),
    (
        r"\binit\s+0\b",
        "System halt via init",
        "shutdown",
    ),

    # ── iptables flush (network security bypass) ──
    (
        r"iptables\s+-F\b",
        "Flushing all iptables firewall rules",
        "firewall_flush",
    ),
    (
        r"iptables\s+-X\b",
        "Deleting all custom iptables chains",
        "firewall_flush",
    ),
    (
        r"ufw\s+disable\b",
        "Disabling UFW firewall",
        "firewall_flush",
    ),

    # ── Overwriting system files ──
    (
        r"echo\s+.*>\s*/etc/(passwd|shadow|sudoers|fstab|hosts)",
        "Overwriting critical system file",
        "file_overwrite",
    ),
    (
        r"cat\s+/dev/null\s*>\s*/etc/(passwd|shadow|sudoers|fstab|hosts)",
        "Truncating critical system file",
        "file_overwrite",
    ),

    # ── Network backdoor / reverse shell ──
    (
        r"bash\s+-i\s*>&\s*/dev/(tcp|udp)/",
        "Reverse shell via bash /dev/tcp",
        "reverse_shell",
    ),
    (
        r"nc\s+.*-e\s+/bin/(sh|bash)",
        "Reverse shell via netcat",
        "reverse_shell",
    ),
    (
        r"python\d?\s+-c\s+.*socket\.socket.*connect",
        "Python reverse shell detected",
        "reverse_shell",
    ),
]

# Compile all patterns once
_COMPILED_PATTERNS: list[tuple[str, str, str]] = [
    (re.compile(pattern, re.IGNORECASE | re.DOTALL), desc, category)
    for pattern, desc, category in DESTRUCTIVE_PATTERNS
]


# ──────────────────────────────────────────────────────────────────── #
# Core logic
# ──────────────────────────────────────────────────────────────────── #

def check_command(command: str) -> tuple[bool, str, str]:
    """Check a bash command for destructive patterns.

    Args:
        command: The bash command string to check.

    Returns:
        Tuple of (is_destructive, description, category).
        If is_destructive is False, description and category are empty strings.
    """
    if not command or not command.strip():
        return False, "", ""

    # Normalize whitespace for matching
    normalized = command.strip()

    for compiled_pattern, description, category in _COMPILED_PATTERNS:
        match = compiled_pattern.search(normalized)
        if match:
            return True, description, category

    return False, "", ""


def process_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Process a PreToolUse event and return a deny response if needed.

    Args:
        event: The parsed JSON event from Claude Code.
            Expected format: {"tool_name": "Bash", "tool_input": {"command": "..."}}

    Returns:
        None if the command is safe (allow).
        A dict with permissionDecision="deny" if the command is destructive.
    """
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        return None

    tool_input = event.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command", "")
    if not command:
        return None

    is_destructive, description, category = check_command(command)
    if not is_destructive:
        return None

    return {
        "permissionDecision": "deny",
        "permissionDecisionReason": f"Blocked: {description} (category: {category})",
    }


def main() -> int:
    """Entry point: read stdin, check command, output response."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            return 0  # No input, allow

        event = json.loads(raw_input)
    except (json.JSONDecodeError, ValueError):
        return 0  # Invalid JSON, allow (don't block on parse errors)

    response = process_event(event)
    if response is None:
        return 0  # Allow

    # Output deny response as JSON to stdout
    print(json.dumps(response))
    return 1  # Deny


if __name__ == "__main__":
    sys.exit(main())
