#!/usr/bin/env python3
"""Claude Code PreToolUse hook that denies destructive shell commands.

Reads the hook payload from stdin. Blocks recursive force deletes, table drops,
truncations, forced pushes and DELETE statements without WHERE, logs every block
to ~/.claude/hooks/blocked.log, and returns a permissionDecision of "deny".
Safe commands produce no output and exit 0. Standard library only.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SHELL_TOOLS = {"Bash", "Shell", "PowerShell"}


def statements(command):
    """Split a shell command into individual statements for scoped checks."""
    return [part.strip() for part in re.split(r"[;\n]|&&|\|\|", command or "") if part.strip()]


def classify(command):
    """Return a short pattern name when a statement is destructive, else None."""
    for statement in statements(command):
        text = statement.strip()

        # rm -rf, rm -fr, rm -r -f (flags may be combined or separate)
        if re.search(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", text, re.I):
            return "recursive force delete"
        if re.search(r"\brm\b", text, re.I) and re.search(r"\s-r(?:\s|$)", text, re.I) and re.search(r"\s-f(?:\s|$)", text, re.I):
            return "recursive force delete"
        if re.search(r"\bRemove-Item\b", text, re.I) and re.search(r"-Recurse\b", text, re.I) and re.search(r"-Force\b", text, re.I):
            return "recursive force delete"

        if re.search(r"\bDROP\s+TABLE\b", text, re.I):
            return "table drop"
        if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", text, re.I):
            return "table truncate"
        if re.search(r"\bgit\s+push\b", text, re.I) and re.search(r"(?:--force(?:-with-lease)?|-f)(?:\s|$)", text, re.I):
            return "forced git push"

        # A DELETE is only safe when the same statement is scoped by WHERE.
        if re.search(r"\bDELETE\s+FROM\b", text, re.I) and not re.search(r"\bWHERE\b", text, re.I):
            return "unscoped delete"

    return None


def log_path():
    override = os.environ.get("CLAUDE_HOOK_LOG")
    return Path(override) if override else Path.home() / ".claude" / "hooks" / "blocked.log"


def record_block(command, project, pattern):
    """Append one JSON line describing a blocked attempt."""
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "attempted_command": command,
        "project_path": project,
        "matched_pattern": pattern,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")
    return entry


def payload_fields(data):
    tool = str(data.get("tool_name", ""))
    tool_input = data.get("tool_input") or {}
    command = str(tool_input.get("command") or data.get("command") or "")
    project = str(data.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return tool, command, project


def main():
    raw = sys.stdin.read()
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError:
        data = {}

    tool, command, project = payload_fields(data)
    if tool and tool not in SHELL_TOOLS:
        return 0

    pattern = classify(command)
    if not pattern:
        return 0

    record_block(command, project, pattern)
    reason = "Blocked {} command: {}".format(pattern, command.strip())
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision, sort_keys=True))
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
