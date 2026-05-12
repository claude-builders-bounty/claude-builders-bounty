#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.
"""
import json
import sys
import re
from datetime import datetime
from pathlib import Path

DANGEROUS_PATTERNS = [
    (r"\brm\s+(-[^\s]*f[^\s]*|-[^\s]*r[^\s]*\s+-[^\s]*f[^\s]*)(\s|$)", "rm with -f flag (destructive delete)"),
    (r"\brm\s+-rf\b", "rm -rf (destructive recursive delete)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE (irreversible database operation)"),
    (r"\bTRUNCATE\b", "TRUNCATE (wipes all rows)"),
    (r"\bgit\s+push\s+[^|&;\n]*--force\b", "git push --force (overwrites remote history)"),
    (r"\bgit\s+push\s+[^|&;\n]*\s-f\b", "git push -f (overwrites remote history)"),
]

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def is_delete_without_where(command: str) -> bool:
    if not re.search(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
        return False
    return not re.search(r"\bWHERE\b", command, re.IGNORECASE)


def log_blocked(command: str, reason: str, cwd: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = (
        f"[{datetime.now().isoformat()}] "
        f"project={cwd!r} | "
        f"reason={reason!r} | "
        f"command={command[:500]!r}\n"
    )
    with LOG_PATH.open("a") as f:
        f.write(entry)


def check_command(command: str) -> tuple[bool, str]:
    """Return (is_dangerous, reason)."""
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            return True, reason
    if is_delete_without_where(command):
        return True, "DELETE FROM without WHERE (deletes all rows)"
    return False, ""


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if data.get("tool_name") != "Bash":
        sys.exit(0)

    command = data.get("tool_input", {}).get("command", "")
    cwd = data.get("cwd", "")

    dangerous, reason = check_command(command)
    if not dangerous:
        sys.exit(0)

    log_blocked(command, reason, cwd)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked by destructive-bash-guard: {reason}. "
                "This command was prevented to protect your data. "
                f"Check {LOG_PATH} for the full log. "
                "If you truly need to run this command, the user must execute it manually."
            ),
        }
    }
    print(json.dumps(output))
    sys.exit(2)


if __name__ == "__main__":
    main()
