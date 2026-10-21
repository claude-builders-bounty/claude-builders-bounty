#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Intercepts dangerous bash commands before execution in Claude Code.

Blocks:
1. Recursive forced removals: `rm -rf`, `rm -fr`, `rm -r -f`
2. Database drops: `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`
3. Force pushes: `git push --force`, `git push -f`, `git push +branch`
4. Table truncations: `TRUNCATE [TABLE]`
5. Blind deletions: `DELETE FROM <table>` without a `WHERE` clause

Logs all blocked attempts to `~/.claude/hooks/blocked.log` with:
- Timestamp (ISO 8601 UTC)
- Attempted command
- Project path
- Rule violated
"""

import sys
import os
import re
import json
from datetime import datetime, timezone

# Path to audit log
LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Destructive pattern definitions: (Regex Pattern, Descriptive Rule Name)
BLOCKED_PATTERNS = [
    (
        re.compile(
            r"(?:^|[\s;&|`])rm\s+(?:[^\s;]*\s+)*-(?=[a-zA-Z]*r)(?=[a-zA-Z]*f)[a-zA-Z]+\b|"
            r"(?:^|[\s;&|`])rm\s+(?:[^\s;]*\s+)*-r\b(?:[^\s;]*\s+)*-f\b|"
            r"(?:^|[\s;&|`])rm\s+(?:[^\s;]*\s+)*-f\b(?:[^\s;]*\s+)*-r\b|"
            r"(?:^|[\s;&|`])rm\s+(?:[^\s;]*\s+)*--(?:recursive\s+--force|force\s+--recursive)\b",
            re.IGNORECASE,
        ),
        "Recursive force removal (rm -rf / rm -fr)",
    ),
    (
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA|VIEW)\b", re.IGNORECASE),
        "Database drop statement (DROP TABLE / DATABASE / SCHEMA)",
    ),
    (
        re.compile(
            r"\bgit\s+push\s+(?:[^\s;]+\s+)*(?:--force|-f\b|--force-with-lease|\+[a-zA-Z0-9_\-\.\/]+)",
            re.IGNORECASE,
        ),
        "Force git push (git push --force / -f / +branch)",
    ),
    (
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\s+[a-zA-Z0-9_\.\"`'\[\]]+", re.IGNORECASE),
        "Database truncation statement (TRUNCATE TABLE)",
    ),
    (
        re.compile(
            r"\bDELETE\s+FROM\s+[a-zA-Z0-9_\.\"`'\[\]]+(?:\s*(?:;|$|\)|&&|\|\|)|(?!\s+WHERE\b))",
            re.IGNORECASE,
        ),
        "Blind SQL deletion (DELETE FROM without WHERE clause)",
    ),
]


def extract_command_and_context():
    """
    Extracts the command string and project directory from:
    1. CLI arguments (direct invocation or test runners)
    2. stdin JSON payload (standard Claude Code hook invocation)
    3. Environment variables (fallback)
    """
    command = ""
    project_path = os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd()

    # 1. Try CLI arguments first if explicitly provided
    if len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    # 2. Try reading JSON from stdin if no CLI arguments and stdin is piped
    if not command and not sys.stdin.isatty():
        try:
            stdin_data = sys.stdin.read().strip()
            if stdin_data:
                try:
                    payload = json.loads(stdin_data)
                    if isinstance(payload, dict):
                        # Extract project path if present
                        if "project_path" in payload:
                            project_path = payload["project_path"]
                        elif "projectPath" in payload:
                            project_path = payload["projectPath"]

                        # Extract tool input command
                        tool_input = payload.get("tool_input") or payload.get("input") or payload
                        if isinstance(tool_input, dict):
                            command = tool_input.get("command") or tool_input.get("cmd") or ""
                        elif isinstance(tool_input, str):
                            command = tool_input
                except json.JSONDecodeError:
                    # Treat raw text on stdin as direct command
                    command = stdin_data
        except Exception:
            pass

    # 3. Fallback to environment variables
    if not command:
        command = os.getenv("CLAUDE_TOOL_COMMAND") or os.getenv("BASH_COMMAND") or ""

    return command.strip(), project_path


def check_destructive_command(command: str):
    """
    Evaluates the command against all blocked patterns.
    Returns (is_blocked: bool, rule_name: str)
    """
    if not command:
        return False, ""

    # Check for DELETE FROM with WHERE clause specifically
    delete_from_match = re.search(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\.\"`'\[\]]+)", command, re.IGNORECASE)
    if delete_from_match:
        # Check if there is a WHERE clause in the query
        remainder = command[delete_from_match.end():]
        # Look for WHERE keyword before any statement terminator or end
        where_match = re.search(r"\bWHERE\b", remainder, re.IGNORECASE)
        if not where_match:
            return True, "Blind SQL deletion (DELETE FROM without WHERE clause)"

    # Check all other patterns
    for pattern, rule_name in BLOCKED_PATTERNS:
        # Skip generic DELETE rule since we handled it above
        if "DELETE FROM" in rule_name:
            continue
        if pattern.search(command):
            return True, rule_name

    return False, ""


def log_blocked_attempt(command: str, project_path: str, rule: str):
    """
    Logs the blocked command details to ~/.claude/hooks/blocked.log
    """
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        log_entry = (
            f"[{timestamp}] [PROJECT: {project_path}] "
            f"BLOCKED: {command} | RULE: {rule}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to write to {LOG_FILE}: {e}\n")


def main():
    command, project_path = extract_command_and_context()

    # If no command detected (e.g. non-bash tool or empty), allow pass-through
    if not command:
        sys.exit(0)

    is_blocked, rule = check_destructive_command(command)

    if is_blocked:
        log_blocked_attempt(command, project_path, rule)

        error_message = (
            "\n"
            "====================================================================\n"
            " [BLOCKED] Claude Code Destructive Command Interceptor\n"
            "====================================================================\n"
            f"Command Attempted : {command}\n"
            f"Rule Triggered    : {rule}\n"
            f"Project Location  : {project_path}\n"
            f"Audit Log File    : {LOG_FILE}\n"
            "--------------------------------------------------------------------\n"
            "SAFETY INVARIANT: Destructive system/database modifications are blocked.\n"
            "To execute this command, run it manually in your external terminal.\n"
            "====================================================================\n"
        )
        sys.stderr.write(error_message)
        # Non-zero exit code halts tool execution in Claude Code
        sys.exit(2)

    # Safe command: exit 0 to allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
