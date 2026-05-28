#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands before execution.

Reads JSON from stdin: {"tool_name": "Bash", "tool_input": {"command": "..."}}
Writes JSON to stdout: {"decision": "allow"|"block", "reason": "..."}
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# ---------------------------------------------------------------------------
# Destructive pattern definitions
# Each entry: (regex, human_readable_description)
# ---------------------------------------------------------------------------

PATTERNS = [
    # rm -rf / variants — dangerous recursive force removal
    (
        re.compile(r"\brm\s+.*-r.*f\b", re.IGNORECASE),
        "rm -rf (recursive force remove) — can irreversibly delete entire directory trees",
    ),
    # DROP TABLE (SQL)
    (
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "DROP TABLE — permanently destroys a database table and all its data",
    ),
    # git push --force (and --force-with-lease)
    (
        re.compile(r"\bgit\s+push\b.*--force", re.IGNORECASE),
        "git push --force — overwrites remote history, erasing teammates' commits",
    ),
    # TRUNCATE (SQL)
    (
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "TRUNCATE — removes all rows from a table without possibility of rollback",
    ),
    # DELETE FROM without WHERE clause — wipes all rows
    (
        re.compile(
            r"\bDELETE\s+FROM\s+\S+(?!.*\bWHERE\b)",
            re.IGNORECASE,
        ),
        "DELETE FROM without WHERE — removes every row from the table",
    ),
]

# ---------------------------------------------------------------------------
# Helper: extract command from tool input
# ---------------------------------------------------------------------------

def extract_command(tool_input):
    """Extract the bash command string from the tool_input dict.

    Claude Code's Bash tool passes the command in 'command'.
    Handle alternate shapes gracefully.
    """
    if isinstance(tool_input, str):
        return tool_input
    if isinstance(tool_input, dict):
        return tool_input.get("command", "") or tool_input.get("cmd", "") or ""
    return ""


# ---------------------------------------------------------------------------
# Helper: log a blocked attempt
# ---------------------------------------------------------------------------

def log_block(project_path, command, reason):
    """Append a structured entry to the block log."""
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"{timestamp} | project={project_path} | "
        f"command={json.dumps(command)} | reason={reason}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Main hook logic
# ---------------------------------------------------------------------------

def main():
    # Read the JSON payload from stdin
    raw = sys.stdin.read()
    if not raw.strip():
        # No input — allow by default
        print(json.dumps({"decision": "allow"}))
        return

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed input — allow (don't break the editor)
        print(json.dumps({"decision": "allow"}))
        return

    tool_name = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {})
    project_path = payload.get("cwd", "") or payload.get("project_path", "") or os.getcwd()

    # Only inspect Bash tool invocations
    if tool_name.lower() != "bash":
        print(json.dumps({"decision": "allow"}))
        return

    command = extract_command(tool_input)

    # Walk through dangerous patterns
    for pattern_regex, description in PATTERNS:
        if pattern_regex.search(command):
            reason = description
            log_block(project_path, command, reason)

            # Clear, terminal-friendly block message
            msg = (
                "\n"
                "╔══════════════════════════════════════════════════════════╗\n"
                "║  ⛔  DESTRUCTIVE COMMAND BLOCKED                         ║\n"
                "╠══════════════════════════════════════════════════════════╣\n"
                f"║  Command : {command[:44]:<44s} ║\n"
                f"║  Reason  : {reason[:44]:<44s} ║\n"
                "╠══════════════════════════════════════════════════════════╣\n"
                "║  This command was intercepted by the safety hook.       ║\n"
                "║  If you are absolutely sure you want to run it,         ║\n"
                "║  execute it manually in your terminal.                  ║\n"
                "╚══════════════════════════════════════════════════════════╝\n"
            )
            # Write the blocking decision
            result = {"decision": "block", "reason": msg}
            print(json.dumps(result))
            return

    # No dangerous pattern matched — allow
    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
