#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive Bash commands.

Reads PreToolUse JSON from stdin. Denies dangerous patterns and appends
a line to ~/.claude/hooks/blocked.log. Safe commands pass through (exit 0).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Ordered (name, compiled pattern, human reason). First match wins.
RULES: list[tuple[str, re.Pattern[str], str]] = [
    (
        "rm -rf",
        re.compile(
            r"(?:^|[\s;&|])rm\s+(?:-[^\s]*f[^\s]*\s+[^\s]*r|[^\s]*r[^\s]*\s+[^\s]*f|"
            r"-[^\s]*rf|[^\s]*fr|--recursive\s+--force|--force\s+--recursive)\b",
            re.IGNORECASE,
        ),
        "Recursive force delete (rm -rf / rm --recursive --force) is blocked by the PreToolUse safety hook.",
    ),
    (
        "rm -rf (compact)",
        re.compile(r"(?:^|[\s;&|])rm\s+-[a-zA-Z]*[rf][a-zA-Z]*[rf][a-zA-Z]*\b", re.IGNORECASE),
        "Recursive force delete (rm -rf) is blocked by the PreToolUse safety hook.",
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "SQL DROP TABLE is blocked by the PreToolUse safety hook.",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b", re.IGNORECASE),
        "SQL TRUNCATE is blocked by the PreToolUse safety hook.",
    ),
    (
        "git push --force",
        re.compile(
            r"\bgit\s+push\b[^\n]*?(?:--force\b|-f\b|--force-with-lease\b)",
            re.IGNORECASE,
        ),
        "Force-push (git push --force / -f) is blocked by the PreToolUse safety hook.",
    ),
    (
        "DELETE FROM without WHERE",
        # DELETE FROM <table> ... end, with no WHERE keyword before end/;/&&/||
        re.compile(
            r"\bDELETE\s+FROM\s+[^\s;]+(?:\s+(?!WHERE\b)[^\s;]+)*\s*(?:;|$|&&|\|\||\n)",
            re.IGNORECASE,
        ),
        "Unconditional DELETE FROM (no WHERE clause) is blocked by the PreToolUse safety hook.",
    ),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command") or ""
        if isinstance(cmd, str):
            return cmd
    # Fallbacks for alternate shapes
    for key in ("command", "cmd"):
        val = payload.get(key)
        if isinstance(val, str):
            return val
    return ""


def match_rule(command: str) -> tuple[str, str] | None:
    # Special-case DELETE: if WHERE is present after DELETE FROM, allow
    for name, pattern, reason in RULES:
        if name.startswith("DELETE"):
            # Find each DELETE FROM occurrence; skip ones that have WHERE before terminator
            for m in re.finditer(r"\bDELETE\s+FROM\b", command, re.IGNORECASE):
                rest = command[m.start() :]
                # Take until ; or end of string / shell operator at top level (simple)
                chunk = re.split(r"[;\n]|\s&&\s|\s\|\|\s", rest, maxsplit=1)[0]
                if re.search(r"\bWHERE\b", chunk, re.IGNORECASE):
                    continue
                return name, reason
            continue
        if pattern.search(command):
            return name, reason
    return None


def append_log(command: str, project_path: str, reason_name: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # One line: timestamp | rule | command | project path
    line = f"{ts}\t{reason_name}\t{command.replace(chr(9), ' ').replace(chr(10), ' ')}\t{project_path}\n"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def deny(reason: str) -> None:
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(out))
    sys.stdout.flush()


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        return 0
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return 0

    tool_name = (payload.get("tool_name") or "").strip()
    # Only gate Bash; ignore other tools
    if tool_name and tool_name not in ("Bash", "bash"):
        return 0

    command = extract_command(payload)
    if not command.strip():
        return 0

    hit = match_rule(command)
    if not hit:
        return 0

    rule_name, reason = hit
    project_path = (
        payload.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    try:
        append_log(command, str(project_path), rule_name)
    except OSError:
        # Still deny even if log write fails
        pass
    deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
