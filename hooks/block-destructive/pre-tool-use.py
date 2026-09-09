#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Blocks: rm -rf, DROP TABLE, TRUNCATE, git push --force, DELETE FROM without WHERE.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.
"""
import json
import os
import re
import sys
import time

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

PATTERNS = [
    (r"rm\s+-[a-z]*r[a-z]*f", "rm -rf (recursive force delete)"),
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bTRUNCATE\b", "TRUNCATE"),
    (r"git\s+push\b(?:(?!\n).)*--force", "git push --force"),
    (r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", "DELETE FROM without a WHERE clause"),
]


def respond(decision, reason=""):
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
        }
    }
    if reason:
        out["hookSpecificOutput"]["permissionDecisionReason"] = reason
    json.dump(out, sys.stdout)
    sys.exit(0)


def main():
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        sys.exit(0)  # unreadable input: never block by accident

    if data.get("tool_name") != "Bash":
        respond("allow")

    command = (data.get("tool_input") or {}).get("command", "") or ""
    project = data.get("cwd") or os.getcwd()

    for pattern, label in PATTERNS:
        if re.search(pattern, command, re.IGNORECASE | re.DOTALL):
            timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            try:
                with open(LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(f"{timestamp} | blocked: {label} | project: {project} | command: {command}\n")
            except OSError:
                pass
            respond(
                "deny",
                f"Blocked destructive command pattern ({label}). "
                "If this is intentional, run it yourself in an interactive terminal "
                "or rewrite it with an explicit, reviewed scope.",
            )

    respond("allow")


if __name__ == "__main__":
    main()
