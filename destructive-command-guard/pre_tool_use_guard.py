#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Command Guard
Intercepts and blocks dangerous bash commands before execution in Claude Code.
"""

import sys
import os
import json
import re
from datetime import datetime, timezone

# Command prefix: start of line, or following command separators (; && || | ` $(), or wrappers (sudo, nohup, etc.)
CMD_PREFIX = r"(?:^|[;&|`\n]|\$\(|\b(?:sudo|nohup|time|exec|xargs)\s+)\s*"

BLOCKED_PATTERNS = [
    {
        "name": "Recursive forced deletion",
        "pattern": re.compile(
            CMD_PREFIX + r"rm\s+(?:-[a-zA-Z0-9]*[rf][a-zA-Z0-9]*\s+|--recursive\b|--force\b)",
            re.IGNORECASE
        ),
        "reason": "Matches 'rm -rf' or equivalent recursive forced file removal."
    },
    {
        "name": "Git force push",
        "pattern": re.compile(
            CMD_PREFIX + r"git\s+push\b.*?(?:--force\b|-f\b|--force-with-lease\b)",
            re.IGNORECASE
        ),
        "reason": "Matches 'git push --force' or '-f' which overwrites remote git history."
    },
    {
        "name": "SQL DROP TABLE",
        "pattern": re.compile(
            r"\bDROP\s+TABLE\b",
            re.IGNORECASE
        ),
        "reason": "Matches destructive SQL DROP TABLE statement."
    },
    {
        "name": "SQL TRUNCATE",
        "pattern": re.compile(
            r"\bTRUNCATE(?:\s+TABLE)?\b",
            re.IGNORECASE
        ),
        "reason": "Matches destructive SQL TRUNCATE statement."
    },
    {
        "name": "SQL DELETE without WHERE clause",
        "pattern": re.compile(
            r"\bDELETE\s+FROM\s+([`\"'\[]?[a-zA-Z0-9_]+[`\"'\]]?)(?:\s*;|\s*$|\s+(?!.*\bWHERE\b))",
            re.IGNORECASE | re.DOTALL
        ),
        "reason": "Matches SQL DELETE statement without an accompanying WHERE clause."
    }
]

def get_log_path() -> str:
    """Returns ~/.claude/hooks/blocked.log, respecting custom CLAUDE_CONFIG_DIR if set."""
    base_dir = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
    hooks_dir = os.path.join(base_dir, "hooks")
    os.makedirs(hooks_dir, exist_ok=True)
    return os.path.join(hooks_dir, "blocked.log")

def log_blocked(command: str, project_path: str, rule_name: str, reason: str, log_file: str = None):
    """Logs the blocked attempt with ISO timestamp, command, project path, and reason."""
    target_log = log_file or get_log_path()
    timestamp = datetime.now(timezone.utc).isoformat()
    log_entry = {
        "timestamp": timestamp,
        "blocked_command": command,
        "project_path": project_path,
        "rule": rule_name,
        "reason": reason
    }
    try:
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"[Guard Warning] Failed to write audit log: {e}\n")

def check_command(command: str) -> tuple[bool, str, str]:
    """
    Evaluates command against destructive patterns.
    Returns (is_blocked, rule_name, reason).
    """
    if not command:
        return False, "", ""

    # Don't inspect arguments of safe informational print commands (echo, printf)
    trimmed = command.strip()
    if trimmed.startswith("echo ") or trimmed.startswith("printf "):
        # Unless chained with destructive command (e.g. echo foo && rm -rf bar)
        if not re.search(r"[;&|`]", command):
            return False, "", ""

    # Unpack nested shell commands (e.g. bash -c "rm -rf /")
    nested_match = re.search(r'(?:bash|sh|zsh)\s+-c\s+[\'"](.*?)[\'"]', command)
    commands_to_check = [command]
    if nested_match:
        commands_to_check.append(nested_match.group(1))

    for cmd in commands_to_check:
        # Check DELETE FROM specifically to ensure no false positives when WHERE is present
        delete_match = re.search(r"\bDELETE\s+FROM\b", cmd, re.IGNORECASE)
        if delete_match:
            if not re.search(r"\bWHERE\b", cmd[delete_match.start():], re.IGNORECASE):
                return True, "SQL DELETE without WHERE clause", "Matches SQL DELETE statement without an accompanying WHERE clause."

        for rule in BLOCKED_PATTERNS:
            if rule["name"] == "SQL DELETE without WHERE clause":
                continue # Handled with custom lookahead above
            if rule["pattern"].search(cmd):
                return True, rule["name"], rule["reason"]

    return False, "", ""

def main():
    payload = {}
    if not sys.stdin.isatty():
        try:
            raw_input = sys.stdin.read()
            if raw_input.strip():
                payload = json.loads(raw_input)
        except Exception:
            pass

    # Extract tool and command
    tool = payload.get("tool") or payload.get("tool_name") or "Bash"
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("cmd") or ""
    elif isinstance(tool_input, str):
        command = tool_input
    else:
        command = ""

    # Fallback to CLI args if stdin did not contain command
    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    project_path = payload.get("project_path") or os.getcwd()

    # Only inspect Bash tool calls
    if tool.lower() in ("bash", "sh", "terminal", "exec"):
        is_blocked, rule_name, reason = check_command(command)
        if is_blocked:
            log_blocked(command, project_path, rule_name, reason)
            sys.stderr.write(
                f"\n[BLOCKED BY PRE-TOOL-USE GUARD]\n"
                f"Destructive bash command intercepted: {command}\n"
                f"Reason: {rule_name} ({reason})\n"
                f"Audit Log: ~/.claude/hooks/blocked.log\n"
                f"Execution denied to prevent accidental data loss.\n\n"
            )
            sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
