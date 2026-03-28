#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Anti-Destructive Command Guard
=============================================================
Intercepts dangerous bash/SQL commands before Claude executes them.

Blocks:
  - rm -rf               : recursive forced deletion
  - DROP TABLE           : irreversible table destruction
  - DROP DATABASE        : destroys entire database
  - DROP SCHEMA          : destroys entire schema
  - git push --force/-f  : rewrites remote history
  - TRUNCATE             : wipes entire tables
  - DELETE FROM without WHERE : deletes all rows
  - fork bomb :(){ ... } : crashes / saturates the system
  - mkfs.*               : formats a block device
  - dd ... of=/dev/...   : writes directly to a block device

Logs every blocked attempt to: ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime

# ── Constants ──────────────────────────────────────────────────────────────────
LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Each entry: (compiled_regex, human_reason)
DANGEROUS_PATTERNS = [
    (
        re.compile(
            # rm with flags containing both r and f (in any order, possibly combined)
            r'\brm\s+('
            r'-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*'   # -rf, -Rf, -rRfF, etc.
            r'|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*'   # -fr, -fR, etc.
            r'|-r\s+-f|-f\s+-r'                   # -r -f or -f -r (separate flags)
            r'|--recursive\s+--force|--force\s+--recursive'  # long-form flags
            r')',
            re.IGNORECASE,
        ),
        (
            "rm -rf detected: recursive forced deletion is irreversible and can destroy "
            "your entire file system. If you truly need to delete recursively, run this "
            "command manually in a terminal after double-checking the target path."
        ),
    ),
    (
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        (
            "DROP TABLE detected: this permanently destroys a database table and all its "
            "data. If intentional, run it manually in a database client with a backup ready."
        ),
    ),
    (
        re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE),
        (
            "DROP DATABASE detected: this permanently destroys an entire database and all "
            "its tables, indexes, and data. If intentional, run it manually in a database "
            "client with a full backup confirmed."
        ),
    ),
    (
        re.compile(r'\bDROP\s+SCHEMA\b', re.IGNORECASE),
        (
            "DROP SCHEMA detected: this permanently destroys a database schema and "
            "everything it contains. If intentional, run it manually with a backup ready."
        ),
    ),
    (
        re.compile(
            r'\bgit\s+push\b.*?(\s--force\b|\s-f\b|\s--force-with-lease\b)',
            re.IGNORECASE | re.DOTALL,
        ),
        (
            "git push --force detected: force-pushing rewrites remote history and can "
            "permanently destroy commits for all collaborators. Run manually after "
            "confirming with your team."
        ),
    ),
    (
        re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
        (
            "TRUNCATE detected: this removes ALL rows from a table instantly and "
            "cannot be rolled back in most configurations. Run manually with a backup."
        ),
    ),
    # Fork bomb: :(){ :|:& };: and common variants
    (
        re.compile(
            r':\s*\(\s*\)\s*\{.*?:\s*\|.*?:.*?&.*?\}|'   # :(){ :|:& };:
            r':\(\)\s*\{\s*\|\s*&\s*\}\s*;',
            re.DOTALL,
        ),
        (
            "Fork bomb detected: this shell construct recursively spawns processes until "
            "the system runs out of resources and crashes. Never run this command."
        ),
    ),
    # mkfs.* — formats/destroys a filesystem on a block device
    (
        re.compile(r'\bmkfs\b', re.IGNORECASE),
        (
            "mkfs detected: this formats a block device, permanently destroying all data "
            "on it. If intentional, run it manually after triple-checking the target device."
        ),
    ),
    # dd writing directly to a block device
    (
        re.compile(r'\bdd\b.*\bof\s*=\s*/dev/', re.IGNORECASE | re.DOTALL),
        (
            "dd of=/dev/... detected: writing directly to a block device can permanently "
            "destroy the filesystem or partition table. Run manually with extreme caution."
        ),
    ),
]


# ── DELETE FROM without WHERE (special case) ─────────────────────────────────
_DELETE_FROM_RE = re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE)
_WHERE_RE = re.compile(r'\bWHERE\b', re.IGNORECASE)


def _check_delete_without_where(command: str):
    """
    Returns a block reason if the command contains DELETE FROM without a WHERE clause.
    Returns None if the command is safe.

    Strategy: for each DELETE FROM occurrence, check whether a WHERE clause
    appears after it in the same statement.
    """
    for match in _DELETE_FROM_RE.finditer(command):
        # Extract everything from the DELETE keyword to the next semicolon (or end)
        after = command[match.start():]
        stmt_end = after.find(";")
        stmt = after if stmt_end == -1 else after[: stmt_end + 1]
        if not _WHERE_RE.search(stmt):
            return (
                "DELETE FROM without WHERE detected: this would delete EVERY row in "
                "the table. Add a WHERE clause to limit the scope, or run manually "
                "with a backup if a full wipe is truly intended."
            )
    return None


# ── Logging ───────────────────────────────────────────────────────────────────
def _log_blocked(command: str, project_path: str, reason: str) -> None:
    """Append a blocked-command entry to the log file."""
    try:
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        # One-line log entry; use repr() for the command to keep newlines escaped
        entry = (
            f"[{timestamp}] BLOCKED"
            f" | project={project_path}"
            f" | reason={reason.split('.')[0]}"   # first sentence only, keeps log terse
            f" | cmd={repr(command)}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(entry)
    except OSError:
        pass  # Never let logging failure break the hook


# ── Decision output ───────────────────────────────────────────────────────────
def _deny(command: str, project_path: str, reason: str) -> None:
    """Emit a deny decision JSON and exit 0 (Claude Code reads the decision from stdout)."""
    _log_blocked(command, project_path, reason)

    full_message = (
        f"⛔  Command blocked by the anti-destructive hook\n\n"
        f"Reason: {reason}\n\n"
        f"Blocked command:\n  {command}\n\n"
        f"What to do:\n"
        f"  • Double-check that this is truly what you want.\n"
        f"  • If needed, run it manually in a terminal (outside Claude Code).\n"
        f"  • All blocked attempts are logged to: ~/.claude/hooks/blocked.log"
    )

    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": full_message,
        }
    }
    print(json.dumps(result))
    sys.exit(0)


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    # 1. Parse JSON input from stdin
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Non-JSON input → not a Bash invocation we understand → allow
        sys.exit(0)

    # 2. Only inspect Bash tool calls
    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command: str = data.get("tool_input", {}).get("command", "")
    project_path: str = data.get("project_path", os.getcwd())

    if not command:
        sys.exit(0)

    # 3. Check fixed patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(command):
            _deny(command, project_path, reason)

    # 4. Special-case: DELETE FROM without WHERE
    reason = _check_delete_without_where(command)
    if reason:
        _deny(command, project_path, reason)

    # 5. Safe — allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
