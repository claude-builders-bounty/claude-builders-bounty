#!/usr/bin/env python3
"""Claude Code PreToolUse hook — blocks destructive bash commands.

Install:
  python3 install.py

This hook intercepts bash commands before execution and blocks dangerous
patterns like rm -rf, DROP TABLE, git push --force, TRUNCATE, and
DELETE FROM without WHERE.

Follows Claude Code hooks spec:
  https://docs.anthropic.com/claude-code/hooks
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────

HOOK_NAME = "destructive-bash-guard"
LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern_name, regex, explanation)
    (
        "rm -rf",
        r"\brm\s+(-[rfR]+|--recursive\b.*?-f\b|-f\b.*?--recursive\b)",
        "Recursive force delete (`rm -rf`) can permanently destroy files. "
        "If intentional, use the full path and add a comment explaining why.",
    ),
    (
        "rm / ",
        r"\brm\s+/\s*(-[rfR]+)?",
        "Deleting the root filesystem (`rm /`) is never safe.",
    ),
    (
        "rm /*",
        r"\brm\s+/\*\s*(-[rfR]+)?",
        "Deleting everything under root (`rm /*`) is never safe.",
    ),
    (
        "git push --force",
        r"\bgit\s+push\s+.*?(?:--force|-f)\b",
        "Force-pushing overwrites remote history and can lose commits for collaborators. "
        "Use `git push --force-with-lease` instead (it's safer).",
    ),
    (
        "DROP TABLE",
        r"\bDROP\s+TABLE\b",
        "`DROP TABLE` permanently deletes database tables and their data. "
        "Use migrations to safely alter or remove tables.",
    ),
    (
        "DROP DATABASE",
        r"\bDROP\s+DATABASE\b",
        "`DROP DATABASE` permanently destroys the entire database.",
    ),
    (
        "TRUNCATE",
        r"\bTRUNCATE\b",
        "`TRUNCATE` removes all rows from a table. If intentional, consider `DELETE FROM` "
        "with a WHERE clause for auditability.",
    ),
    (
        "DELETE FROM without WHERE",
        r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)",
        "`DELETE FROM` without a `WHERE` clause will remove all rows from the table. "
        "Add a WHERE clause or use TRUNCATE if that's the intent.",
    ),
    (
        "chmod -R 777",
        r"\bchmod\s+(?:-R?\s+)?777\b",
        "Wide-open permissions (`chmod 777`) are a security risk. Use the minimum "
        "required permissions (755 for dirs, 644 for files).",
    ),
    (
        "shutdown / reboot",
        r"\b(?:shutdown|reboot|halt|poweroff)\b",
        "Shutting down or rebooting the system affects all users and running processes.",
    ),
    (
        "> /dev/sda",
        r"\b>\s+/dev/(?:sd[a-z]\d*|nvme\d+n\d+p\d)",
        "Writing directly to block devices can corrupt the filesystem.",
    ),
    (
        "dd to block device",
        r"\bdd\s+.*of=/dev/(?:sd[a-z]\d*|nvme\d+n\d+p\d)",
        "`dd` to a block device can overwrite disk data or partitions.",
    ),
    (
        "curl | bash (pipe to shell)",
        r"\bcurl\s+.*\|\s*(?:bash|sh|zsh)\b",
        "Piping a curl response directly to a shell (`curl URL | bash`) is a security "
        "risk. Download and inspect the script first.",
    ),
    (
        "wget | bash (pipe to shell)",
        r"\bwget\s+.*\|\s*(?:bash|sh|zsh)\b",
        "Piping a wget response directly to a shell is a security risk.",
    ),
    (
        "mkfs / format",
        r"\bmkfs\b|:\bmke2fs\b|\bmkswap\b",
        "Creating filesystems (`mkfs`) destroys existing data on the target device.",
    ),
]


def check_command(command: str) -> list[tuple[str, str]]:
    """Check a command against dangerous patterns.

    Returns list of (pattern_name, explanation) for all matches.
    """
    matches = []
    for name, pattern, explanation in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matches.append((name, explanation))
    return matches


def log_blocked(command: str, matches: list[tuple[str, str]], cwd: str | None = None) -> None:
    """Log a blocked command attempt to the log file."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "project_path": cwd or os.getcwd(),
        "matched_patterns": [m[0] for m in matches],
        "hook": HOOK_NAME,
    }
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        # Logging is best-effort — don't crash the hook
        print(f"[{HOOK_NAME}] Warning: could not write to log: {e}", file=sys.stderr)


def deny_decision(matches: list[tuple[str, str]]) -> str:
    """Generate a deny decision JSON for Claude Code."""
    lines: list[dict] = []
    for name, explanation in matches:
        lines.append({
            "type": "text",
            "text": f"🔒 **Blocked: {name}**\n\n{explanation}",
        })
    lines.append({
        "type": "text",
        "text": (
            "This command was blocked by the **Destructive Bash Guard** hook.\n\n"
            "If you need to run this command:\n"
            "  1. Explain why it's safe in the current context\n"
            "  2. The user can temporarily disable the hook with:\n"
            "     `mv ~/.claude/hooks/block-destructive-bash.py ~/.claude/hooks/block-destructive-bash.py.disabled`\n"
            "  3. Re-enable later: reverse the rename"
        ),
    })

    return json.dumps({"decision": "deny", "message": lines})


def main() -> int:
    """Hook entry point — reads from stdin, writes to stdout."""
    # Read the tool-use payload from stdin
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(f"Failed to parse hook payload: {e}", file=sys.stderr)
        # Allow through on parse error to avoid blocking all commands
        print(json.dumps({"decision": "allow"}))
        return 0

    # Extract the command and arguments
    command = ""
    cwd = None

    if isinstance(payload, dict):
        # PreToolUse format for {command, arguments}
        command = payload.get("command") or payload.get("input", "")
        cwd = payload.get("cwd") or payload.get("workingDirectory")
    elif isinstance(payload, list):
        # Some hook formats pass a list
        command = " ".join(str(p) for p in payload)

    if not command or not command.strip():
        # No command to check — allow
        print(json.dumps({"decision": "allow"}))
        return 0

    matches = check_command(command)

    if not matches:
        # No dangerous patterns matched — allow
        print(json.dumps({"decision": "allow"}))
        return 0

    # Log the blocked attempt
    log_blocked(command, matches, cwd)

    # Return deny decision
    print(deny_decision(matches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
