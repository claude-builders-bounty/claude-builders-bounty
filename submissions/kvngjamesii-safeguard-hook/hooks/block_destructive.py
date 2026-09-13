#!/usr/bin/env python3
"""
Claude Code PreToolUse hook — block destructive bash before execution.

Reads tool-use JSON from stdin. On match: deny via hookSpecificOutput and
append a line to ~/.claude/hooks/blocked.log
  timestamp | attempted command | project path
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Patterns required by bounty #3 + a few high-signal cousins
RULES: list[tuple[str, re.Pattern[str]]] = [
    (
        "Recursive delete (`rm -rf` / `rm -fr`) is blocked",
        re.compile(r"(?:^|[\s;|&])rm\s+(?:-[^\s]*[rfR]|--recursive).*|rm\s+.*(?:-[rfR]{1,3})", re.I),
    ),
    (
        "`DROP TABLE` is blocked",
        re.compile(r"\bDROP\s+TABLE\b", re.I),
    ),
    (
        "`TRUNCATE` is blocked",
        re.compile(r"\bTRUNCATE\b", re.I),
    ),
    (
        "`git push --force` / `-f` is blocked",
        re.compile(r"\bgit\s+push\b[^\n]*?(?:--force\b|--force-with-lease\b|\s-f\b)", re.I),
    ),
    (
        "`DELETE FROM` without a WHERE clause is blocked",
        re.compile(r"\bDELETE\s+FROM\s+\S+(?:\s*;|\s*$|\s+(?!WHERE\b))", re.I),
    ),
]


def extract_command(payload: dict) -> str:
    ti = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(ti, dict):
        for key in ("command", "cmd", "bash"):
            if ti.get(key):
                return str(ti[key])
    # Some hook payloads nest under "input"
    inp = payload.get("input") or {}
    if isinstance(inp, dict) and inp.get("command"):
        return str(inp["command"])
    return ""


def project_path(payload: dict) -> str:
    for key in ("cwd", "cwd_path", "project_dir", "PROJECT_DIR"):
        if payload.get(key):
            return str(payload[key])
    env = payload.get("env") or {}
    if isinstance(env, dict) and env.get("CLAUDE_PROJECT_DIR"):
        return str(env["CLAUDE_PROJECT_DIR"])
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def is_delete_without_where(cmd: str) -> bool:
    """Stricter DELETE FROM ... check that allows DELETE FROM t WHERE ..."""
    for m in re.finditer(r"\bDELETE\s+FROM\s+(\S+)(.*)$", cmd, re.I | re.S):
        rest = m.group(2) or ""
        # strip trailing comments/semicolons for the check
        rest_stripped = re.sub(r"--.*$", "", rest, flags=re.M).strip().rstrip(";").strip()
        if not re.match(r"(?i)^WHERE\b", rest_stripped):
            return True
    return False


def match_reason(cmd: str) -> str | None:
    if not cmd.strip():
        return None
    # Dedicated DELETE logic (regex alone is brittle across shells)
    if is_delete_without_where(cmd):
        return "`DELETE FROM` without a WHERE clause is blocked"
    for reason, pat in RULES:
        if "DELETE FROM" in reason:
            continue
        if pat.search(cmd):
            return reason
    return None


def log_block(cmd: str, path: str) -> None:
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # single-line, pipe-delimited as specified
    safe_cmd = cmd.replace("\n", "\\n")
    line = f"{ts} | {safe_cmd} | {path}\n"
    with log_file.open("a", encoding="utf-8") as f:
        f.write(line)


def deny(reason: str) -> dict:
    msg = (
        f"BLOCKED by safeguard PreToolUse hook: {reason}. "
        "Use a safer alternative (scoped delete, migration with WHERE, or "
        "`git push` without --force)."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": msg,
        },
        "systemMessage": msg,
    }


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed input — do not block the session
        return 0

    tool = (payload.get("tool_name") or payload.get("toolName") or "").lower()
    # Only constrain Bash; never interfere with Read/Edit/etc.
    if tool and tool not in ("bash", "shell"):
        return 0

    cmd = extract_command(payload)
    reason = match_reason(cmd)
    if not reason:
        return 0

    path = project_path(payload)
    try:
        log_block(cmd, path)
    except OSError as e:
        # Still deny even if logging fails
        print(f"[safeguard] log failed: {e}", file=sys.stderr)

    json.dump(deny(reason), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
