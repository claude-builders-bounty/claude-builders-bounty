#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Block Destructive Bash Commands

Intercepts Bash tool calls in Claude Code and blocks dangerous patterns
before they execute.

Installation:
    1. Copy this file to your project root or global hooks directory:
       cp block-destructive-bash.py ~/.claude/hooks/

    2. Register in .claude/settings.json or project settings:
       {
         "hooks": {
           "PreToolUse": [
             {
               "matcher": "Bash",
               "command": "python3 /path/to/block-destructive-bash.py"
             }
           ]
         }
       }

Blocked patterns (regex-based, case-insensitive partial match):
    - rm -rf /, rm -rf ~, rm -rf /*        (recursive root/home delete)
    - dd if=/dev/                            (disk destruction)
    - mkfs                                   (filesystem format)
    - fork bomb (:(){ :|:& };:)             (process explosion)
    - curl | bash, wget | bash, sh -c $(...) (remote code execution)
    - shutdown, reboot, halt, poweroff       (system shutdown)
    - iptables, ufw                          (firewall rules that can lock out)
    - > /dev/sda                             (overwrite disk)
    - chmod -R 777 /                         (permission chaos)
    - :(){:|:&};:, fork()                   (fork bombs, alternate syntax)

Exit codes:
    0 → Allow (command is safe)
    1 → Block (command matched a dangerous pattern)

Stdin: JSON { "tool_name": "...", "input": { "command": "..." } }
Stdout: JSON { "decision": "allow|deny", "reason": "..." }
"""

from __future__ import annotations

import json
import re
import sys

# ── Dangerous patterns ────────────────────────────────────────────────
# Each entry: (compiled regex, human-readable description)
DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # ── Destructive file operations ──
    (
        re.compile(r"rm\s+-rf?\s+[/~]|rm\s+-rf?\s+/\s*", re.IGNORECASE),
        "Recursive delete of root or home directory (rm -rf / or rm -rf ~)",
    ),
    (
        re.compile(r"rm\s+-rf?\s+--no-preserve-root\s*/", re.IGNORECASE),
        "Root directory deletion with --no-preserve-root",
    ),
    # ── Disk destruction ──
    (
        re.compile(r"dd\s+if=/dev/", re.IGNORECASE),
        "Low-level disk write via dd (data destruction)",
    ),
    (
        re.compile(r"mkfs\.", re.IGNORECASE),
        "Filesystem formatting (mkfs.*)",
    ),
    (
        re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
        "Direct raw disk overwrite",
    ),
    # ── Remote code execution ──
    (
        re.compile(r"(curl|wget)\s+.*(\|\s*(bash|sh)|\s*>\s*/(dev/shm|tmp)/.*\s*&&\s*(bash|sh))", re.IGNORECASE),
        "Remote script execution pipeline (curl/wget | bash)",
    ),
    (
        re.compile(r"sh\s+-c\s*\$\(.*(curl|wget)", re.IGNORECASE),
        "Remote code execution via subshell",
    ),
    # ── System control ──
    (
        re.compile(r"\b(shutdown|reboot|halt|poweroff|init\s+0)\b", re.IGNORECASE),
        "System shutdown/reboot command",
    ),
    # ── Firewall lockout risk ──
    (
        re.compile(r"(iptables|ufw)\s+.*(-F|--flush|-P\s+INPUT\s+DROP)", re.IGNORECASE),
        "Firewall rule that may lock out all access",
    ),
    # ── Permission chaos ──
    (
        re.compile(r"chmod\s+-R\s+777\s+/", re.IGNORECASE),
        "World-writable root filesystem (chmod -R 777 /)",
    ),
    # ── Fork bombs ──
    (
        re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;", re.IGNORECASE),
        "Fork bomb pattern detected",
    ),
    (
        re.compile(r"fork\(\)\s*\{", re.IGNORECASE),
        "Fork bomb (C-style) pattern detected",
    ),
]


def check_command(command: str) -> tuple[bool, str]:
    """
    Check a shell command against dangerous patterns.

    Returns:
        (is_safe, reason) — if is_safe=False, reason explains why it was blocked.
    """
    # Strip leading/trailing whitespace and collapse inner whitespace for matching
    cleaned = command.strip()

    # Empty commands are safe
    if not cleaned:
        return True, ""

    for pattern, description in DANGEROUS_PATTERNS:
        if pattern.search(cleaned):
            return False, description

    return True, ""


def main() -> int:
    """Claude Code hook entry point. Reads JSON from stdin, outputs decision."""
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            # No input = allow by default (fail-open for non-hook contexts)
            print(json.dumps({"decision": "allow", "reason": "No input provided"}))
            return 0

        data = json.loads(raw_input)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("input", {})

        # Only intercept Bash tool calls
        if tool_name != "Bash":
            print(json.dumps({"decision": "allow", "reason": f"Not a Bash call ({tool_name})"}))
            return 0

        command = tool_input.get("command", "")
        is_safe, reason = check_command(command)

        if is_safe:
            output = {"decision": "allow", "reason": "Command passed safety check"}
        else:
            output = {
                "decision": "deny",
                "reason": f"🚫 BLOCKED: {reason}\nCommand: {command[:200]}",
            }

        print(json.dumps(output))
        return 0 if is_safe else 1

    except json.JSONDecodeError as e:
        # If we cannot parse input, allow (fail-open to avoid breaking workflows)
        print(json.dumps({"decision": "allow", "reason": f"Invalid JSON input: {e}"}))
        return 0
    except Exception as e:
        print(json.dumps({"decision": "allow", "reason": f"Hook error: {e}"}), file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
