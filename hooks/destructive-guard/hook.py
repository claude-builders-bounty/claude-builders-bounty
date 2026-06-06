#!/usr/bin/env python3
"""
destructive-guard — Claude Code PreToolUse hook.
Intercepts dangerous bash commands and blocks them before execution.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# ── Pattern definitions ────────────────────────────────────────────────────────

_SQL_DROP     = re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE)
_SQL_TRUNCATE = re.compile(r'\bTRUNCATE\b', re.IGNORECASE)
_SQL_DELETE   = re.compile(r'\bDELETE\s+FROM\s+\S+', re.IGNORECASE)
_SQL_WHERE    = re.compile(r'\bWHERE\b', re.IGNORECASE)
_GIT_FORCE    = re.compile(r'\bgit\s+push\b.*?(\s--force(?!-)|\s-f\b)', re.IGNORECASE)
_DD_DISK      = re.compile(r'\bdd\b.*\bof=/dev/', re.IGNORECASE)
_FORK_BOMB    = re.compile(r':\(\s*\)\s*\{.*:\s*\|.*:.*&.*\}')  # :(){ :|:& };


def _is_rm_rf(command: str) -> bool:
    """True if command contains rm with both -r and -f flags (any order/combination)."""
    for m in re.finditer(r'\brm\s+((?:-\S+\s+)*-\S+)', command):
        flags = "".join(re.findall(r'-([A-Za-z]+)', m.group(1))).lower()
        if "r" in flags and "f" in flags:
            return True
    return False


def _is_delete_without_where(command: str) -> bool:
    """True for DELETE FROM … with no WHERE clause."""
    return bool(_SQL_DELETE.search(command)) and not bool(_SQL_WHERE.search(command))


def is_blocked(command: str) -> tuple[bool, str]:
    """Return (blocked, reason). Reason is '' when not blocked."""
    if _is_rm_rf(command):
        return True, "rm -rf / rm -fr: recursive force-delete is irreversible"
    if _SQL_DROP.search(command):
        return True, "DROP TABLE: permanently destroys a database table"
    if _SQL_TRUNCATE.search(command):
        return True, "TRUNCATE: removes all rows from a table without WHERE"
    if _is_delete_without_where(command):
        return True, "DELETE FROM without WHERE: would delete every row in the table"
    if _GIT_FORCE.search(command):
        return True, "git push --force: rewrites remote history and can destroy others' work"
    if _DD_DISK.search(command):
        return True, "dd of=/dev/*: overwrites raw disk device, destroys partition data"
    if _FORK_BOMB.search(command):
        return True, "fork bomb detected: :(){ :|:& }; exhausts all processes and crashes the system"
    return False, ""


# ── Logging ────────────────────────────────────────────────────────────────────

def log_blocked(command: str, reason: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "reason": reason,
        "command": command,
        "project_path": os.getcwd(),
    }
    with LOG_FILE.open("a") as f:
        f.write(json.dumps(entry) + "\n")


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)  # malformed input — don't interfere

    if not isinstance(data, dict) or data.get("tool_name") != "Bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = data.get("tool_input", {}).get("command", "")
    blocked, reason = is_blocked(command)

    if blocked:
        log_blocked(command, reason)
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"🚫 destructive-guard blocked this command.\n"
                f"Reason: {reason}\n"
                f"Logged to: {LOG_FILE}"
            ),
        }))
    else:
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
