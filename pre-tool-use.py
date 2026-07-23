#!/usr/bin/env python3
"""pre-tool-use hook — blocks destructive commands before execution."""
import os
import sys
from datetime import datetime

# Patterns that get blocked (case-insensitive match)
BLOCKED = [
    "rm -rf",
    "rm -fr",
    "rm -r -f",
    "rm -f -r",
    "rm --recursive --force",
    "init 0",
    "init 6",
    "shutdown",
    "reboot",
    "> /dev/sda",
    "> /dev/nvme",
    "mkfs.",
    "dd if=",
    ":(){ :|:& };:",  # fork bomb
]

# Patterns that get flagged (warn but don't block)
DANGEROUS_SQL = ["drop table", "truncate", "delete from"]
DANGEROUS_GIT = ["git push --force", "git push -f", "git push --force-with-lease"]


def read_input():
    """Read the input payload from stdin up to 16KB."""
    return sys.stdin.read(16384)


def parse_payload(payload: dict) -> tuple:
    """Extract command and working directory from hook payload."""
    tool_use = payload.get("tool_use", {})
    command = ""
    cwd = ""

    if tool_use.get("name") == "Bash":
        command = tool_use.get("input", {}).get("command", "")
        cwd = tool_use.get("input", {}).get("cwd", os.getcwd())
    elif tool_use.get("name") == "BashInteractive":
        command = tool_use.get("input", {}).get("command", "")

    return command.strip(), cwd or os.getcwd()


def log_blocked(command: str, cwd: str, reason: str):
    """Append a blocked/failed command to the log file."""
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "blocked.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] [{reason}] cmd={command} | cwd={cwd}\n"
    with open(log_path, "a") as f:
        f.write(entry)


def is_delete_without_where(command: str) -> bool:
    """Check if a DELETE FROM lacks a WHERE clause."""
    lower = command.lower()
    if "delete from" not in lower:
        return False
    # Find WHERE after the last DELETE FROM
    idx = lower.rfind("delete from")
    rest = lower[idx:]
    return " where " not in rest and ";--where" not in rest  # allow inline-comment WHERE


def check_command(command: str, cwd: str) -> dict:
    """Return block/veto decision. Empty = allow."""
    lower = command.lower()

    # Exact blocked patterns
    for pattern in BLOCKED:
        if pattern in lower:
            log_blocked(command, cwd, f"blocked: {pattern}")
            return {
                "veto": True,
                "message": (
                    f"⚠️  Command blocked for safety: `{pattern}` detected.\n"
                    f"This pattern is destructive and was intercepted by the pre-tool-use hook.\n"
                    f"If you really mean to run this, disable the hook temporarily:\n"
                    f"  mv ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py.disabled"
                ),
            }

    # Dangerous SQL without WHERE
    for pattern in DANGEROUS_SQL:
        if pattern in lower and is_delete_without_where(command):
            log_blocked(command, cwd, "blocked: DELETE without WHERE")
            return {
                "veto": True,
                "message": (
                    f"⚠️  Command blocked: `{pattern}` without a WHERE clause.\n"
                    f"This would modify/delete ALL rows in the table.\n"
                    f"Add a WHERE clause to target specific rows."
                ),
            }

    # Force push warning (block, it's destructive)
    for pattern in DANGEROUS_GIT:
        if pattern in lower:
            log_blocked(command, cwd, f"blocked: {pattern}")
            return {
                "veto": True,
                "message": (
                    f"⚠️  Command blocked: force push detected.\n"
                    f"Force push rewrites remote history and affects all collaborators.\n"
                    f"Use `git revert` or `git push --force-with-lease` with explicit confirmation instead."
                ),
            }

    return {}


def main():
    raw = read_input()
    try:
        import json
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Not a JSON hook payload — allow
        print(json.dumps({"veto": False}))
        sys.exit(0)

    command, cwd = parse_payload(payload)
    if command:
        result = check_command(command, cwd)
        print(json.dumps(result))
    else:
        print(json.dumps({"veto": False}))


if __name__ == "__main__":
    main()
