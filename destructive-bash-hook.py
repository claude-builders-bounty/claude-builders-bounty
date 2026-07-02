#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Bash Command Guard

Blocks dangerous bash commands before execution.
Part of the $100 bounty: https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

Usage:
    1. Place this file at ~/.claude/hooks/pre_tool_use.py
    2. Or register via claude.json:
       {"pre_tool_use_hooks": [{"command": "python3 ~/.claude/hooks/pre_tool_use.py"}]}

    The hook receives the tool use payload as JSON on stdin and must
    return a JSON response on stdout.
"""

import json
import sys
import re
import os
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked_commands.log")

# ── Deny list ──────────────────────────────────────────────────────────
# Each entry is a (pattern, risk_level, reason) tuple.
# Patterns are regex, case-insensitive by default.

DENY_RULES = [
    # System destruction
    (r'\brm\s+-rf\s+/\s*$', 'critical', 'Recursive force-delete of entire filesystem'),
    (r'\brm\s+-rf\s+/\s+--no-preserve-root', 'critical', 'Filesystem deletion without root protection'),
    (r'\bmkfs\.', 'critical', 'Filesystem creation/formatting commands'),
    (r'\bdd\s+if=.+\s+of=/dev/', 'critical', 'Direct device writes via dd'),
    (r'>\s*/dev/sda', 'critical', 'Direct device write'),

    # Database destruction
    (r'\bDROP\s+DATABASE\b', 'critical', 'Database deletion'),
    (r'\bDROP\s+TABLE\b', 'critical', 'Table deletion'),
    (r'\bTRUNCATE\s+TABLE\b', 'high', 'Table truncation'),
    (r'\bDROP\s+USER\b', 'high', 'User account deletion'),
    (r'\bDROP\s+INDEX\b', 'medium', 'Index deletion'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', 'critical', 'Unconditional row deletion (no WHERE clause)'),
    (r'\bUPDATE\s+\w+\s+SET\b(?!.*\bWHERE\b)', 'high', 'Unconditional update (no WHERE clause)'),

    # Network security
    (r'\biptables\s+-F\b', 'critical', 'Flush all iptables rules (opens firewall)'),
    (r'\biptables\s+-P\s+INPUT\s+ACCEPT\b', 'high', 'Open firewall INPUT chain'),
    (r'\bpasswd\s+-d\b', 'critical', 'Remove password for user account'),
    (r'\buseradd\s+-[a-z]*0', 'medium', 'Create user with UID 0 (root-equivalent)'),
    (r'\busermod\s+-[a-z]*0', 'medium', 'Change user to UID 0'),

    # Shell/production safety
    (r'\bchmod\s+-R\s+777\s+/', 'critical', 'Recursive world-writable permissions on root'),
    (r'\bchown\s+-R\s+.*?:.*?:?\s+/', 'high', 'Recursive ownership change starting at root'),
    (r'\bkillall\s+(?!-w\b)', 'medium', 'Kill all processes of a name (may kill critical services)'),
    (r'\bkill\s+-9\s+-1\b', 'critical', 'Kill all user processes'),
    (r'\bshutdown\s+-h\s+now\b', 'critical', 'Immediate system shutdown'),
    (r'\breboot\b', 'medium', 'System reboot'),
    (r'\bpoweroff\b', 'medium', 'System power off'),

    # Crypto/mining (likely compromise)
    (r'\bwget\s+.*(?:crypt|coin|miner|xmrig)\b', 'medium', 'Cryptocurrency miner download'),
    (r'\bcurl\s+.*(?:crypt|coin|miner|xmrig)\b', 'medium', 'Cryptocurrency miner download'),
    (r'\bpkexec\s+', 'high', 'Potential privilege escalation via pkexec'),

    # Package management destructive actions
    (r'\bapt\s+(?:remove|purge)\s+--purge\b', 'high', 'Destructive package removal'),
    (r'\bdpkg\s+--purge\b', 'high', 'Destructive package removal'),
]


class DestructiveBashHook:
    """Pre-tool-use hook that blocks dangerous bash commands."""

    def __init__(self):
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    def check_command(self, command: str) -> dict:
        """
        Check a bash command against the deny list.

        Returns:
            {"allowed": True} if the command is safe,
            {"allowed": False, "reason": "...", "risk": "..."} if blocked.
        """
        if not isinstance(command, str) or not command.strip():
            return {"allowed": True}

        # Check against all deny rules
        for pattern, risk, reason in DENY_RULES:
            if re.search(pattern, command, re.IGNORECASE | re.MULTILINE):
                self._log_block(command, reason, risk)
                return {
                    "allowed": False,
                    "reason": reason,
                    "risk": risk,
                    "message": (
                        f"🛑 Blocked: {reason}\n"
                        f"   Risk: {risk.upper()}\n"
                        f"   Command: {command[:200]}\n"
                        "   To allow, add the command to the whitelist or modify the pattern."
                    )
                }

        return {"allowed": True}

    def _log_block(self, command: str, reason: str, risk: str) -> None:
        """Log a blocked command attempt."""
        try:
            with open(LOG_FILE, "a") as f:
                f.write(
                    f"[{datetime.now().isoformat()}] "
                    f"RISK={risk.upper()} "
                    f"REASON={reason} "
                    f"CMD={command[:200]}\n"
                )
        except Exception:
            pass

    def handle(self) -> None:
        """
        Read tool use payload from stdin, check the command, respond on stdout.

        Expected input (from Claude Code):
            {"tool_use": {"name": "Bash", "input": {"command": "rm -rf /"}}}

        Response:
            {"allowed": True} or {"allowed": False, "reason": "..."}
        """
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError:
            # If we can't parse, allow (fail open is safer for hook errors)
            json.dump({"allowed": True}, sys.stdout)
            return

        # Extract the command from the payload
        tool_use = payload.get("tool_use", {})
        tool_name = tool_use.get("name", "")
        tool_input = tool_use.get("input", {})

        if tool_name == "Bash":
            command = tool_input.get("command", "")
            result = self.check_command(command)
            json.dump(result, sys.stdout)
        else:
            # Not a bash command — allow
            json.dump({"allowed": True}, sys.stdout)


if __name__ == "__main__":
    hook = DestructiveBashHook()
    hook.handle()
