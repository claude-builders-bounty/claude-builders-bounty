#!/usr/bin/env python3
"""
Destructive Command Guard — Claude Code pre-tool-use hook

Blocks destructive bash commands before they can execute.
Zero dependencies, Python 3.7+.

Install:
  cp hooks/pre-tool-use/destructive-command-guard.py .claude/hooks/pre-tool-use/
  chmod +x .claude/hooks/pre-tool-use/destructive-command-guard.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


# ── Dangerous command patterns ──────────────────────────────────────────────

DANGEROUS_PATTERNS = [
    # rm -rf (and variants like rm -r -f, rm --recursive --force)
    {
        "id": "RM_RF",
        "description": "Recursive force delete",
        "pattern": re.compile(
            r'\brm\s+(?:-[rfRF]+|--recursive\s+--force|--force\s+--recursive|-r\s+-f|-f\s+-r)\b',
            re.IGNORECASE,
        ),
        "suggestion": "Use a trash/bin directory instead of rm -rf. Consider 'mv <path> /tmp/trash/'",
    },
    # git push --force (and -f)
    {
        "id": "GIT_PUSH_FORCE",
        "description": "Force push to git remote",
        "pattern": re.compile(r'\bgit\s+push\s+(?!.*--force-with-lease\b).*?(?:--force|-f)\b', re.IGNORECASE),
        "suggestion": "Use 'git push --force-with-lease' instead — it refuses if your remote-tracking branch is out of date",
    },
    # DROP TABLE (SQL)
    {
        "id": "DROP_TABLE",
        "description": "SQL DROP TABLE statement",
        "pattern": re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        "suggestion": "Use DROP TABLE IF EXISTS with a backup first, or use RENAME TO <table>_backup as a safety net",
    },
    # DROP DATABASE
    {
        "id": "DROP_DATABASE",
        "description": "SQL DROP DATABASE statement",
        "pattern": re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE),
        "suggestion": "Never DROP DATABASE in production. Create a backup and rename instead",
    },
    # TRUNCATE (SQL)
    {
        "id": "TRUNCATE",
        "description": "SQL TRUNCATE statement",
        "pattern": re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
        "suggestion": "Use DELETE with a WHERE clause, or backup before TRUNCATE",
    },
    # DELETE FROM without WHERE
    {
        "id": "DELETE_WITHOUT_WHERE",
        "description": "SQL DELETE FROM without a WHERE clause",
        "pattern": re.compile(r'\bDELETE\s+FROM\b', re.IGNORECASE),
        "check_where": True,
        "suggestion": "Add a WHERE clause! Without WHERE, this deletes ALL rows. Use SELECT first to verify scope",
    },
    # dd command (dangerous disk operations)
    {
        "id": "DD_DANGEROUS",
        "description": "dd command targeting block devices",
        "pattern": re.compile(r'\bdd\s+.*\bof=\s*/(?:dev/)?(?:sd[a-z]|nvme\d+n\d+|hd[a-z])\b', re.IGNORECASE),
        "suggestion": "dd to block devices can destroy data. Double-check the 'of=' target",
    },
    # chmod -R 777
    {
        "id": "CHMOD_777_RECURSIVE",
        "description": "Recursive chmod to 777",
        "pattern": re.compile(r'\bchmod\s+-R\s+777\b', re.IGNORECASE),
        "suggestion": "chmod -R 777 is a security risk. Set specific permissions (e.g., 755 for dirs, 644 for files)",
    },
    # chown -R (recursive ownership change)
    {
        "id": "CHOWN_RECURSIVE",
        "description": "Recursive ownership change",
        "pattern": re.compile(r'\bchown\s+-R\b', re.IGNORECASE),
        "suggestion": "chown -R can break system permissions. Target specific paths",
    },
    # > /dev/sda and similar direct disk writes
    {
        "id": "DIRECT_DISK_WRITE",
        "description": "Direct write to block device",
        "pattern": re.compile(r'(?:>|>>|\|)\s*/dev/(?:sd[a-z]|nvme\d+n\d+|hd[a-z]|sda)'),
        "suggestion": "Writing directly to a block device destroys all data on it",
    },
    # mkfs / format commands
    {
        "id": "MKFS",
        "description": "Filesystem creation command",
        "pattern": re.compile(r'\b(?:mkfs\.\w+|mkfs|format)\s+/dev/', re.IGNORECASE),
        "suggestion": "mkfs destroys all data on the target. Triple-check the device",
    },
    # :(){ :|:& };: — fork bomb
    {
        "id": "FORK_BOMB",
        "description": "Fork bomb / denial of service",
        "pattern": re.compile(r'[:\{\}\\]+\|\s*[:\{\}\\]+\s*&?\s*;', re.IGNORECASE),
        "suggestion": "Fork bombs crash the system. Never run this",
    },
    # Wipe/erase/shred commands
    {
        "id": "SHRED",
        "description": "File shredding",
        "pattern": re.compile(r'\bshred\s+', re.IGNORECASE),
        "suggestion": "shred permanently destroys data. It cannot be undone",
    },
]


# ── Logging ─────────────────────────────────────────────────────────────────

def get_log_path():
    """Return the path to the guard log file."""
    env_log = os.environ.get("DESTRUCTIVE_GUARD_LOG")
    if env_log:
        return Path(env_log)
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        base = Path(xdg)
    else:
        base = Path.home() / ".local" / "share"
    return base / "destructive-command-guard" / "guard.log"


def log_attempt(cmd, matched_pattern, project_path):
    """Log a blocked destructive command attempt."""
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": cmd,
        "matched_pattern": matched_pattern["id"],
        "description": matched_pattern["description"],
        "project_path": str(project_path),
        "suggestion": matched_pattern["suggestion"],
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


# ── Detection ───────────────────────────────────────────────────────────────

def check_command(cmd):
    """
    Check a command string against all dangerous patterns.

    Returns (is_dangerous, matched_pattern, log_entry).
    """
    if not cmd or not cmd.strip():
        return False, None, None

    project_path = Path.cwd()

    # Normalize: strip shell comments (lines starting with #)
    normalized = cmd.strip()
    if normalized.startswith("#"):
        return False, None, None

    # Skip detection for echo commands — they only display text
    if re.match(r'\becho\b', normalized, re.IGNORECASE):
        return False, None, None

    for pattern_def in DANGEROUS_PATTERNS:
        match = pattern_def["pattern"].search(normalized)
        if not match:
            continue

        # Special check: DELETE FROM must be without WHERE
        if pattern_def.get("check_where"):
            # Look for a WHERE clause after the DELETE FROM
            after_match = normalized[match.end():]
            if re.search(r'\bWHERE\b', after_match, re.IGNORECASE):
                continue  # Has WHERE, not dangerous

        log_entry = log_attempt(cmd, pattern_def, project_path)
        return True, pattern_def, log_entry

    return False, None, None


def print_blocked(pattern, log_entry):
    """Print a clear block message to stderr."""
    print(
        f"\n"
        f"╔══ BLOCKED BY DESTRUCTIVE COMMAND GUARD ══╗\n"
        f"  Pattern:  {pattern['description']} ({pattern['id']})\n"
        f"  Command:  {log_entry['command'][:120]}\n"
        f"  Project:  {log_entry['project_path']}\n"
        f"  Time:     {log_entry['timestamp']}\n"
        f"  Suggestion: {pattern['suggestion']}\n"
        f"  Logged to: {get_log_path()}\n"
        f"╚════════════════════════════════════════════╝\n",
        file=sys.stderr,
    )


# ── Main entry points ───────────────────────────────────────────────────────

def main_cli():
    """
    CLI entry point: check a command string passed as argument.
    Usage: destructive-command-guard.py "rm -rf /some/path"
    """
    if len(sys.argv) < 2:
        cmd = sys.stdin.read().strip()
    else:
        cmd = " ".join(sys.argv[1:])

    is_dangerous, pattern, log_entry = check_command(cmd)

    if is_dangerous:
        print_blocked(pattern, log_entry)
        sys.exit(1)

    sys.exit(0)


def main_stdin_json():
    """
    Claude Code hook entry point: read tool call JSON from stdin.

    The hook receives a JSON object like:
      {"tool": "Bash", "args": {"command": "rm -rf /"}, ...}

    Returns JSON with allowed/blocked decision.
    """
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except (json.JSONDecodeError, Exception):
        # Not JSON or empty — fall back to CLI mode
        main_cli()
        return

    # Try to extract command from various tool formats
    cmd = None
    if "args" in data and isinstance(data["args"], dict):
        cmd = data["args"].get("command") or data["args"].get("cmd") or data["args"].get("script")
    if not cmd and "command" in data:
        cmd = data["command"]
    if not cmd and "tool_input" in data:
        cmd = data["tool_input"]

    if not cmd:
        # No command found — allow by default
        print(json.dumps({"allowed": True}))
        return

    is_dangerous, pattern, log_entry = check_command(cmd)

    if is_dangerous:
        result = {
            "allowed": False,
            "reason": f"Blocked: {pattern['description']} — {pattern['suggestion']}",
            "matched_pattern": pattern["id"],
        }
        print(json.dumps(result))
        sys.exit(1)
    else:
        print(json.dumps({"allowed": True}))
        sys.exit(0)


if __name__ == "__main__":
    # Auto-detect mode: if stdin has JSON, use hook mode
    if not sys.stdin.isatty():
        try:
            peek = sys.stdin.read(1)
            if peek:
                sys.stdin = os.fdopen(0, "r")  # Re-open stdin
                # Check if it looks like JSON
                import select
                if peek in ("{", "["):
                    main_stdin_json()
                else:
                    main_cli()
            else:
                sys.exit(0)
        except Exception:
            main_cli()
    else:
        main_cli()
