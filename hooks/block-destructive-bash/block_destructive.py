#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code: Blocks destructive bash commands.
Complies with Claude Code hook specification (~/.claude/hooks/).
Bounty #3 implementation for Claude Builders.
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional

# Path to the security audit log
LOG_DIR = Path(os.environ.get("CLAUDE_HOOKS_DIR", Path.home() / ".claude" / "hooks"))
LOG_FILE = LOG_DIR / "blocked.log"

# Destructive pattern rules: (regex pattern, rule description)
BLOCKED_PATTERNS = [
    (
        r"(?:^|[;&|\s])(?:sudo\s+)?rm\s+.*(?:-[a-zA-Z0-9]*[rR][a-zA-Z0-9]*[fF]|-[a-zA-Z0-9]*[fF][a-zA-Z0-9]*[rR]|--recursive\s+--force|--force\s+--recursive)",
        "Recursive file deletion (rm -rf / rm --recursive)"
    ),
    (
        r"(?:^|[;&|\s])(?:sudo\s+)?rm\s+.*(?:-[a-zA-Z0-9]*[rR]\b.*-[a-zA-Z0-9]*[fF]\b|-[a-zA-Z0-9]*[fF]\b.*-[a-zA-Z0-9]*[rR]\b)",
        "Recursive file deletion (rm -r -f)"
    ),
    (
        r"\bDROP\s+(?:DATABASE|SCHEMA|TABLE|VIEW)\b",
        "Destructive SQL DROP operation"
    ),
    (
        r"\bgit\s+push\b.*(?:\s+-f\b|\s+--force\b|\s+--force-with-lease\b)",
        "Force-push to git repository"
    ),
    (
        r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_`\"\[\]]+",
        "Destructive SQL TRUNCATE operation"
    ),
]


def strip_sql_comments(query: str) -> str:
    """Strips SQL block comments /* ... */ and line comments -- ..."""
    no_block = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)
    no_line = re.sub(r"--.*$", " ", no_block, flags=re.MULTILINE)
    return no_line


def check_command_safety(command: str) -> Tuple[bool, Optional[str]]:
    """
    Analyzes a command string against destructive patterns.
    Returns: (is_safe: bool, reason_if_blocked: Optional[str])
    """
    if not command or not command.strip():
        return True, None

    normalized = command.strip()

    # Check for unbounded SQL DELETE: has DELETE FROM but lacks WHERE outside comments
    if re.search(r"\bDELETE\s+FROM\b", normalized, re.IGNORECASE):
        cleaned_sql = strip_sql_comments(normalized)
        if not re.search(r"\bWHERE\b", cleaned_sql, re.IGNORECASE):
            return False, "Unbounded SQL DELETE without a WHERE clause"

    for pattern, description in BLOCKED_PATTERNS:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, description

    return True, None



def log_blocked_attempt(command: str, reason: str, project_path: str):
    """Logs the blocked command attempt to ~/.claude/hooks/blocked.log."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        log_entry = (
            f"[{timestamp}] BLOCKED: {reason}\n"
            f"  Command: {command}\n"
            f"  Project: {project_path}\n"
            f"{'-' * 60}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[WARNING] Could not write to audit log: {e}\n")


def extract_command() -> Tuple[str, str]:
    """
    Extracts command from stdin (JSON from Claude Code hook) or sys.argv.
    Returns: (command_string, project_path)
    """
    project_path = os.getcwd()

    # 1. Check CLI argument first
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]), project_path

    # 2. Check stdin (Claude Code JSON hook payload)
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw and raw.strip():
                try:
                    data = json.loads(raw)
                    # Claude Code pre-tool-use passes:
                    # {"tool_name": "Bash", "tool_input": {"command": "..."}}
                    tool_input = data.get("tool_input", {})
                    command = tool_input.get("command", "")
                    project_path = data.get("project_path", data.get("cwd", project_path))
                    return command, project_path
                except json.JSONDecodeError:
                    # Raw string passed via stdin
                    return raw.strip(), project_path
        except Exception:
            pass

    return "", project_path


def main():
    command, project_path = extract_command()

    if not command:
        # Empty command or non-command tool call, allow
        sys.exit(0)

    is_safe, reason = check_command_safety(command)

    if not is_safe:
        log_blocked_attempt(command, reason, project_path)

        message = (
            f"\n🛡️ [CLAUDE SECURITY HOOK BLOCKED]\n"
            f"Reason:  {reason}\n"
            f"Command: {command}\n"
            f"Path:    {project_path}\n"
            f"Action:  Execution was intercepted and aborted before execution.\n"
            f"Log:     {LOG_FILE}\n"
        )
        sys.stderr.write(message)
        # Non-zero exit code aborts the tool execution in Claude Code
        sys.exit(2)

    # Safe command allowed to proceed
    sys.exit(0)


if __name__ == "__main__":
    main()
