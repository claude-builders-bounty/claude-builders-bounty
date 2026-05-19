#!/usr/bin/env python3
"""
pre-tool-use hook for Claude Code — intercepts dangerous bash commands.

Blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE FROM without WHERE.
Logs every blocked attempt. Non-blocking for all other commands.

Installation (2 commands):
    mkdir -p ~/.claude/hooks
    cp pre_tool_use.py ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use

Configure in Claude Code settings or .claude/settings.json:
    {"hooks": {"PreToolUse": [{"command": "~/.claude/hooks/pre_tool_use"}]}}
"""

import json
import sys
import os
import re
from datetime import datetime, timezone


LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def log_blocked(command: str, reason: str, project_path: str = ""):
    """Append blocked command to log file."""
    ensure_log_dir()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project_path or 'N/A'} | reason={reason} | command={command}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception as e:
        print(f"Warning: could not write to log: {e}", file=sys.stderr)


def check_destructive(command: str, project_path: str = "") -> tuple[bool, str]:
    """
    Check if a command is destructive. Returns (is_destructive, reason).
    """
    cmd_stripped = command.strip()
    cmd_lower = cmd_stripped.lower()

    patterns = [
        # rm -rf variants
        (r"\brm\s+.*-r.*f\b", "rm -rf (recursive force remove)"),
        (r"\brm\s+.*-rf\b", "rm -rf (recursive force remove)"),
        (r"\brm\s+.*--recursive.*--force\b", "rm --recursive --force"),
        # DROP TABLE
        (r"\bdrop\s+table\b", "DROP TABLE (database table deletion)"),
        # TRUNCATE
        (r"\btruncate\s+(table\s+)?\w", "TRUNCATE (table truncation)"),
        # DELETE FROM without WHERE
        (r"\bdelete\s+from\s+\w+\s*(?:;|$)", "DELETE FROM without WHERE clause"),
        (r"\bdelete\s+from\s+\w+\s+where\b", None),  # has WHERE — allow
        # git push --force variants
        (r"\bgit\s+push\s+.*(--force|-f)\b", "git push --force (force push)"),
        (r"\bgit\s+push\s+--delete\b", "git push --delete (branch deletion)"),
        # Dangerous filesystem ops
        (r"\bchmod\s+.*777\b", "chmod 777 (world-writable permission)"),
        (r"\bdd\s+if=.*of=/dev/\w", "dd writing to device directly"),
        (r">\s*/dev/sd[a-z]", "redirect to raw block device"),
        # Fork bomb
        (r":\(\)\s*\{.*:.*\|.*:.*&.*\}", "fork bomb pattern"),
    ]

    # Check DELETE FROM with WHERE separately (whitelist, not block)
    delete_with_where = re.search(r"\bdelete\s+from\s+\w+\s+where\b", cmd_lower)
    delete_without_where = re.search(r"\bdelete\s+from\s+\w+\s*(?:;|$)", cmd_lower)

    for pattern, reason in patterns:
        if reason is None:
            continue
        if re.search(pattern, cmd_lower):
            # Exception: DELETE FROM with WHERE should not be blocked
            if "delete" in pattern.lower() and "where" in reason.lower():
                continue
            return True, reason

    # Special: DELETE FROM without WHERE
    if delete_without_where and not delete_with_where:
        return True, "DELETE FROM without WHERE clause"

    return False, ""


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # No input or invalid — allow by default
        output = {"decision": "allow"}
        print(json.dumps(output))
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", "")

    # Only intercept bash/terminal commands
    if tool_name not in ("bash", "execute_command", "run_shell_command", "terminal", "Bash"):
        output = {"decision": "allow"}
        print(json.dumps(output))
        sys.exit(0)

    # Extract command from various input formats
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "") or tool_input.get("cmd", "") or tool_input.get("input", "")
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        output = {"decision": "allow"}
        print(json.dumps(output))
        sys.exit(0)

    is_destructive, reason = check_destructive(command, project_path)

    if is_destructive:
        log_blocked(command, reason, project_path)
        message = (
            f"🛡️  BLOCKED: This command was intercepted by the safety hook.\n"
            f"    Reason: {reason}\n"
            f"    Command: {command}\n"
            f"    If you are absolutely sure this is safe, bypass the hook or use a safer alternative."
        )
        output = {
            "decision": "deny",
            "reason": message,
        }
        print(json.dumps(output), file=sys.stderr)
        print(json.dumps(output))
        sys.exit(1)

    # Allow
    output = {"decision": "allow"}
    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
