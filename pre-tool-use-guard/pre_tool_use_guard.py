#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pre_tool_use_guard.py — Claude Code PreToolUse hook
=====================================================
Blocks destructive bash commands BEFORE execution, logs every blocked
attempt, and never interferes with normal commands.

Install (2 commands):
  mkdir -p ~/.claude/hooks
  cp pre_tool_use_guard.py ~/.claude/hooks/ && python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home()/".claude"/"settings.json"
cfg = json.loads(p.read_text()) if p.exists() else {}
cfg.setdefault("hooks", {}).setdefault("PreToolUse", []).append(
    {"matcher": "Bash", "hooks": [{"type": "command",
     "command": "python3 ~/.claude/hooks/pre_tool_use_guard.py"}]})
p.write_text(json.dumps(cfg, indent=2))
print("installed")
PY

Protocol: reads a JSON event on stdin, writes a JSON decision on stdout.
"""
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# ---------------------------------------------------------------------------
# Blocking rules. Each rule returns a human-readable reason or None (allowed).
# ---------------------------------------------------------------------------
RULES = [
    # rm -rf (recursive force delete)
    (re.compile(r"\brm\s+(-{1,2}[a-zA-Z]*[rf][a-zA-Z]*\s+)*[^\s;|&]*", re.I),
     "rm -rf style recursive force delete"),

    # DROP TABLE / DROP DATABASE
    (re.compile(r"\bdrop\s+(table|database|schema|index|view)\b", re.I),
     "DROP TABLE/DATABASE/SCHEMA"),

    # git push --force / -f
    (re.compile(r"\bgit\s+push\b[^|;&]*?(--force|-f\b)", re.I),
     "git push --force"),

    # TRUNCATE
    (re.compile(r"\btruncate\s+table\b", re.I),
     "TRUNCATE TABLE"),

    # DELETE FROM without WHERE
    (re.compile(r"\bdelete\s+from\b[^;|&]*(?<!where\b)[^;|&]*$", re.I),
     "DELETE FROM without WHERE clause"),
]


def evaluate(command: str):
    """Return (blocked: bool, reason: str)."""
    cmd = command.strip()
    lowered = cmd.lower()

    if re.search(r"\brm\s+(-{1,2}[a-z]*r[a-z]*f[a-z]*)\b", lowered):
        return True, "rm -rf (recursive force delete)"

    if re.search(r"\brm\s+(-{1,2}[a-z]*f[a-z]*r[a-z]*)\b", lowered):
        return True, "rm -fr (recursive force delete)"

    if re.search(r"\bdrop\s+(table|database|schema|index|view)\b", lowered):
        return True, "DROP TABLE/DATABASE/SCHEMA/INDEX/VIEW"

    if re.search(r"\bgit\s+push\b[^;|&]*?(--force\b|(?<![\w-])-f\b)", lowered):
        return True, "git push --force"

    if re.search(r"\btruncate\s+table\b", lowered):
        return True, "TRUNCATE TABLE"

    if re.search(r"\bdelete\s+from\b", lowered) and not re.search(r"\bwhere\b", lowered):
        return True, "DELETE FROM without WHERE clause"

    return False, ""


def log_block(attempted: str, reason: str, cwd: str):
    """Append a blocked attempt to the log file (atomic-ish append)."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = json.dumps({
            "timestamp": ts,
            "reason": reason,
            "attempted_command": attempted,
            "project_path": cwd,
        }, ensure_ascii=False)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        # Never crash Claude because logging failed.
        pass


def main():
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        # Not a valid hook event: allow silently.
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionReason": "invalid event payload",
        }}))
        return 0

    tool_input = event.get("tool_input") or {}
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command") or tool_input.get("prompt") or ""
    if not command:
        command = event.get("tool_name") or ""

    cwd = event.get("cwd") or os.getcwd()
    blocked, reason = evaluate(command)

    if not blocked:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionReason": "command is safe",
        }}))
        return 0

    log_block(command, reason, cwd)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionReason": f"Blocked by pre-tool-use guard: {reason}. "
                            "Ask the user for explicit approval before running this.",
    }}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    main()
