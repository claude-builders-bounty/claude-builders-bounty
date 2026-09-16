#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Block Destructive Bash Commands
Fulfills Bounty #3 on claude-builders-bounty ($100).

Intercepts dangerous commands before execution, logs blocked events,
and emits clear actionable diagnostics for Claude and developers.
"""

import sys
import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path

# Prohibited dangerous patterns
PROHIBITED_PATTERNS = [
    (r"\brm\s+.*?(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive\s+.*--force|--force\s+.*--recursive|-r\b.*-f\b|-f\b.*-r\b)", "rm -rf (Recursive forced directory removal)"),
    (r"(?i)\bdrop\s+table\b", "DROP TABLE (Database table destruction)"),
    (r"\bgit\s+push\s+.*?(?:--force\b|-f\b|--force-with-lease\b)", "git push --force (Remote git history overwrite)"),
    (r"(?i)\btruncate\s+(?:table\s+)?[a-zA-Z0-9_]+", "TRUNCATE (Table data wipe)"),
    (r"(?i)\bdelete\s+from\s+[a-zA-Z0-9_`\"']+(?!\s+where\b)(?:\s*;|\s*$)", "DELETE FROM without WHERE clause (Unconditional table purge)"),
]

def get_log_path() -> Path:
    override = os.environ.get("CLAUDE_HOOK_LOG_PATH")
    if override:
        return Path(override)
    home = Path.home()
    return home / ".claude" / "hooks" / "blocked.log"

def log_blocked_attempt(command: str, reason: str, cwd: str) -> None:
    try:
        log_file = get_log_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_line = f"[{timestamp}] REASON: {reason} | CWD: {cwd} | CMD: {command}\n"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_line)
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to write to blocked.log: {e}\n")

def inspect_command(command: str, cwd: str = ".") -> tuple[bool, str]:
    for pattern, description in PROHIBITED_PATTERNS:
        if re.search(pattern, command):
            return False, description
    return True, ""

def main():
    raw_input = ""
    if len(sys.argv) > 1:
        raw_input = " ".join(sys.argv[1:])
    elif not sys.stdin.isatty():
        raw_input = sys.stdin.read().strip()

    if not raw_input:
        sys.exit(0)

    command = ""
    # Support Claude Code JSON hook payload format
    if raw_input.startswith("{"):
        try:
            data = json.loads(raw_input)
            tool_name = data.get("tool_name", "")
            if tool_name and tool_name != "bash":
                sys.exit(0)
            command = data.get("tool_input", {}).get("command", "")
            if not command and "command" in data:
                command = data["command"]
        except json.JSONDecodeError:
            command = raw_input
    else:
        command = raw_input

    if not command:
        sys.exit(0)

    cwd = os.getcwd()
    is_safe, reason = inspect_command(command, cwd)

    if not is_safe:
        log_blocked_attempt(command, reason, cwd)
        error_message = (
            f"\n🚨 [CLAUDE CODE SECURITY GUARD: COMMAND BLOCKED]\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Reason:  Destructive command prohibited: {reason}\n"
            f"Command: {command}\n"
            f"Path:    {cwd}\n"
            f"Logged:  {get_log_path()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Action: Command was intercepted and stopped before execution.\n"
            f"To proceed safely, verify your command or perform changes manually.\n\n"
        )
        sys.stderr.write(error_message)
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
