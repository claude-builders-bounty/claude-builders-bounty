#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook that blocks destructive bash commands.

Receives JSON tool call data on stdin, checks for dangerous patterns,
and returns a permission decision via stdout JSON.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
SYSTEM_PATHS = {"/", "/bin", "/boot", "/dev", "/etc", "/home", "/lib",
                "/media", "/mnt", "/opt", "/proc", "/root", "/sbin",
                "/srv", "/sys", "/tmp", "/usr", "/var"}

# ── Detection Rules ────────────────────────────────────────────────────────

def check_command(cmd: str) -> tuple[str, str] | None:
    """
    Check a bash command for destructive patterns.
    Returns (decision_reason, log_message) if blocked, None if allowed.
    """
    stripped = cmd.strip()

    # --- rm -rf targeting system paths ---
    m = re.search(r'\brm\s+(-[rfv]+\s+)*(-rf|-[rf]+|--recursive\s+(-f|--force)?)\s+(.+)', stripped, re.IGNORECASE)
    if m:
        target = m.group(m.lastindex).strip().split()[0] if m.lastindex else ""
        # Resolve relative paths
        abs_target = os.path.abspath(os.path.expanduser(target)) if target else ""
        # Check if targeting root or a system directory
        if target in ("/",) or abs_target in SYSTEM_PATHS or any(abs_target.startswith(p + "/") for p in SYSTEM_PATHS if p != "/"):
            return (
                f"Blocking `rm -rf` on system path: {target}",
                f"rm -rf on system path: {target}"
            )

    # --- rm -rf with dangerous flags on / ---
    if re.search(r'\brm\s+(-[rfv]+\s+)*-[rf]+\s+[/\\]', stripped):
        return (
            "Blocking `rm -rf` on root directory",
            "rm -rf targeting root /"
        )

    # --- DROP TABLE ---
    if re.search(r'\bdrop\s+table\b', stripped, re.IGNORECASE):
        return (
            "Blocking `DROP TABLE` — would destroy a database table",
            "DROP TABLE detected"
        )

    # --- git push --force (not --force-with-lease) ---
    if re.search(r'\bgit\s+push\b', stripped, re.IGNORECASE):
        if re.search(r'\b--force\b(?!\s*-\s*with-lease)', stripped):
            return (
                "Blocking `git push --force`. Use `--force-with-lease` instead — it's safer.",
                "git push --force detected"
            )

    # --- TRUNCATE ---
    if re.search(r'\btruncate\s+table\b', stripped, re.IGNORECASE):
        return (
            "Blocking `TRUNCATE` — would erase all rows from a database table",
            "TRUNCATE TABLE detected"
        )

    # --- DELETE FROM without WHERE ---
    if re.search(r'\bdelete\s+from\b', stripped, re.IGNORECASE):
        has_where = re.search(r'\bwhere\b', stripped, re.IGNORECASE)
        if not has_where:
            return (
                "Blocking `DELETE FROM` without a WHERE clause — would delete all rows",
                "DELETE FROM without WHERE detected"
            )

    return None  # Command is safe


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # If we can't parse stdin, allow the command through
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}, sys.stdout)
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only check Bash tool calls
    if tool_name != "Bash" or not command:
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}, sys.stdout)
        sys.exit(0)

    result = check_command(command)

    if result is None:
        # Command is safe — allow
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}, sys.stdout)
        sys.exit(0)
    else:
        reason, log_msg = result

        # Log the blocked attempt
        cwd = data.get("cwd", "unknown")
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_entry = f"[{timestamp}] project={cwd} command={command!r} reason={log_msg}\n"

        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)

        # Return deny decision with clear message
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)


if __name__ == "__main__":
    main()
