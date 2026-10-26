#!/usr/bin/env python3
"""block-destructive.py — Claude Code PreToolUse hook.

Reads the hook JSON event from stdin. If a Bash command matches a destructive
pattern (rm -rf, DROP TABLE, git push --force, TRUNCATE, DELETE without WHERE),
it BLOCKS the command, logs the attempt to ~/.claude/hooks/blocked.log, and
explains why. Normal commands are allowed untouched.

Claude Code hook contract:
  stdin : {"tool_name": "...", "tool_input": {"command": "...", ...}}
  stdout: {"decision": "block"|"approve",
           "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                  "permissionDecision": "deny"|"allow",
                                  "permissionDecisionReason": "..."}}
"""
import json
import os
import re
import sys
from datetime import datetime

LOG_DIR = os.path.join(os.path.expanduser("~"), ".claude", "hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# (compiled pattern, human label) — order matters for the reason message.
RULES = [
    (re.compile(r"\brm\s+-rf\b|\brm\s+-r\s+-f\b|\brm\s+--recursive\b.*-f", re.I),
     "recursive force delete (rm -rf)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "DROP TABLE"),
    (re.compile(r"\bgit\s+push\b[^\n]*--force\b|\bgit\s+push\b[^\n]*--force-with-lease\b",
                re.I), "force push (git push --force)"),
    (re.compile(r"\bTRUNCATE\b\s+\w+", re.I), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b[^\n]*(?!WHERE)", re.I | re.S),
     "DELETE without a WHERE clause"),
]


def log_block(command: str, reason: str) -> None:
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        ts = datetime.now().isoformat(timespec="seconds")
        cwd = os.getcwd()
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{ts}\tcommand={command}\tpath={cwd}\treason={reason}\n")
    except OSError:
        pass  # logging must never break the hook


def decide(command: str):
    for pat, label in RULES:
        if pat.search(command):
            return False, label
    return True, None


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    # Only inspect Bash tool invocations.
    if tool_name == "Bash" and command:
        allowed, label = decide(command)
        if not allowed:
            log_block(command, label)
            print(json.dumps({
                "decision": "block",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked by security hook: matched '{label}'. "
                        "This is a destructive operation. If you are certain, "
                        "re-run with an explicit, scoped, reversible command "
                        "(e.g. target a specific file, or use a transaction/"
                        "backup first)."
                    ),
                },
            }))
            return 0

    # Allow everything else.
    print(json.dumps({"decision": "approve"}))
    return 0


if __name__ == "__main__":
    main()
