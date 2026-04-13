#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code — blocks destructive bash commands.

Reads JSON from stdin (Claude Code hook format), checks the bash command
against a denylist of dangerous patterns, and returns JSON indicating
whether the command should be allowed or blocked.

Usage:
    chmod +x hook.py
    # Claude Code will invoke this automatically when installed to ~/.claude/hooks/

Test:
    echo '{"tool":"bash","args":{"command":"rm -rf /"}}' | python3 hook.py
"""

import json
import re
import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

BLOCKED_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# ─── Dangerous pattern definitions ───────────────────────────────────────────
# Each tuple: (compiled regex, human-readable label)

_PATTERNS = [
    # Recursive force delete — bare / or ~
    (re.compile(r"\brm\s+-(?:rf|rfr|fr)\s+/\s*(?:$|[;&|])", re.IGNORECASE),
     "Recursive force delete from root"),
    (re.compile(r"\brm\s+-(?:rf|rfr|fr)\s+~\s*(?:$|[;&|])", re.IGNORECASE),
     "Recursive force delete from home"),
    (re.compile(r"\brm\s+-(?:rf|rfr|fr)\s+\*\s*(?:$|[;&|])", re.IGNORECASE),
     "Recursive force delete with wildcard"),
    (re.compile(r"\brm\s+-(?:rf|rfr|fr)\s+\.\s*(?:$|[;&|])", re.IGNORECASE),
     "Recursive force delete of current directory"),
    # Recursive force delete of critical system directories
    (re.compile(r"\brm\s+-(?:rf|rfr|fr)\s+/(?:etc|usr|boot|sys|proc|dev|sbin|bin|home|var|opt|root|lib)(?:\s|/|$)", re.IGNORECASE),
     "Recursive force delete of system directory"),

    # SQL destructive statements
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
     "DROP TABLE — destroys table and data"),
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE),
     "DROP DATABASE — destroys entire database"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
     "TRUNCATE TABLE — deletes all rows"),
    (re.compile(r"\bTRUNCATE\b(?!\s+TABLE)", re.IGNORECASE),
     "TRUNCATE — clears table data"),
    (re.compile(r"\bDELETE\s+FROM\s+\S+\s*;", re.IGNORECASE),
     "DELETE FROM without WHERE clause"),
    (re.compile(r"\bDELETE\s+FROM\s+\S+\s+WHERE\s+1\s*=\s*1", re.IGNORECASE),
     "DELETE FROM WHERE 1=1 — deletes all rows"),

    # Git force operations
    (re.compile(r"\bgit\s+push\b.*\s+--force\b", re.IGNORECASE),
     "git push --force — overwrites remote history"),
    (re.compile(r"\bgit\s+push\b.*\s+-f\b(?![-\w])", re.IGNORECASE),
     "git push -f — overwrites remote history"),
    (re.compile(r"\bgit\s+push\s+-f\b", re.IGNORECASE),
     "git push -f — overwrites remote history"),
    (re.compile(r"\bgit\s+reset\s+--hard\s+HEAD~", re.IGNORECASE),
     "git reset --hard — discards commits"),
    (re.compile(r"\bgit\s+clean\s+-ffd\b", re.IGNORECASE),
     "git clean -ffd — removes all untracked files"),

    # Disk/filesystem destruction
    (re.compile(r"\bdd\s+.*of=/dev/(?:sd|nvme|vd)", re.IGNORECASE),
     "dd writing to block device — disk wipe"),
    (re.compile(r"\bmkfs\.", re.IGNORECASE),
     "mkfs — formats a filesystem"),
    (re.compile(r"\bfdisk\b", re.IGNORECASE),
     "fdisk — disk partitioning tool"),
    (re.compile(r"\bwipefs\b", re.IGNORECASE),
     "wipefs — wipes filesystem signatures"),
    (re.compile(r"\bshred\b", re.IGNORECASE),
     "shred — securely deletes files"),

    # Network/firewall destruction
    (re.compile(r"\biptables\s+-F\b", re.IGNORECASE),
     "iptables -F — flushes firewall rules"),
    (re.compile(r"\bufw\s+(?:disable|reset)", re.IGNORECASE),
     "ufw disable/reset — disables firewall"),

    # Fork bomb
    (re.compile(r":\(\)\s*\{.*\|.*\}.*:", re.IGNORECASE),
     "Fork bomb — crashes system"),

    # Privilege escalation hazards
    (re.compile(r"\bchmod\s+777\s+/", re.IGNORECASE),
     "chmod 777 on root — insecure permissions"),
    (re.compile(r"\bchown\s+.*-R\s+/", re.IGNORECASE),
     "Recursive chown on root directory"),

    # Process hazards
    (re.compile(r"\bkill\s+-9\s+1\b"),
     "kill -9 PID 1 — kills init process"),
    (re.compile(r"\bkillall\s+-9\b", re.IGNORECASE),
     "killall -9 — kills all matching processes"),
]


def extract_command(data: dict) -> str | None:
    """Extract the bash command string from Claude Code hook input."""
    tool_name = data.get("tool", data.get("name", ""))
    if tool_name not in ("bash", "Bash", "terminal", ""):
        return None

    args = data.get("args", data.get("input", {}))
    if isinstance(args, dict):
        return args.get("command", args.get("command_line", ""))
    if isinstance(args, str):
        return args
    return None


def check_command(command: str) -> tuple[bool, str | None]:
    """
    Check a command against all blocked patterns.
    Returns (is_allowed, reason_or_none).
    """
    for pattern, label in _PATTERNS:
        if pattern.search(command):
            return False, f"⛔ BLOCKED: {label}"
    return True, None


def log_blocked(command: str, reason: str) -> None:
    """Append a blocked attempt to the log file."""
    try:
        BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        cwd = os.getcwd()
        with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {reason} | cmd: {command} | cwd: {cwd}\n")
    except OSError:
        pass  # Don't fail the hook if logging fails


def main() -> None:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            print(json.dumps({"allow": True}))
            return

        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # If we can't parse input, allow (fail-open for safety)
        print(json.dumps({"allow": True}))
        return

    command = extract_command(data)
    if command is None:
        # Not a bash command — allow
        print(json.dumps({"allow": True}))
        return

    allowed, reason = check_command(command)
    if allowed:
        print(json.dumps({"allow": True}))
    else:
        log_blocked(command, reason)
        print(json.dumps({
            "allow": False,
            "reason": (
                f"{reason}\n\n"
                f"Command: {command}\n\n"
                f"This command was blocked by the pre-tool-use safety hook.\n"
                f"If this is intentional, you can:\n"
                f"  1. Disable the hook: mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.bak\n"
                f"  2. Modify the command to be less destructive\n"
                f"  3. Review the blocked log: cat ~/.claude/hooks/blocked.log"
            ),
        }))


if __name__ == "__main__":
    main()
