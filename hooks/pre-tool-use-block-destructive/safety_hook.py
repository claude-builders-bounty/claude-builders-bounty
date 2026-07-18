#!/usr/bin/env python3
"""
pre-tool-use safety hook for Claude Code.

Blocks dangerous bash commands in `Bash` tool invocations and logs every
blocked attempt to ~/.claude/hooks/blocked.log with timestamp, attempted
command, and project path.

Install:
    # from this repo
    mkdir -p ~/.claude/hooks
    cp hooks/pre-tool-use-block-destructive/safety_hook.py ~/.claude/hooks/
    chmod +x ~/.claude/hooks/safety_hook.py

Then wire into ~/.claude/settings.json:

    {
      "hooks": {
        "PreToolUse": [
          { "matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/safety_hook.py"}] }
        ]
      }
    }

The hook reads the tool-use invocation as JSON on stdin (per Anthropic's hook
spec — see https://docs.anthropic.com/claude-code/hooks), inspects the
command field for destructive patterns, and either:

    * exits 0 to allow the command, or
    * exits 2 with a stderr message to Claude telling it why the command was
      blocked (per Anthropic's contract, exit code 2 = blocking response)

Logs are written to ~/.claude/hooks/blocked.log in append mode.
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path(os.path.expanduser("~/.claude/hooks/blocked.log"))

# Each rule: (compiled regex, human description for the message back to Claude).
# Order matters — first match wins the message.
_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-rf|-fr)\b|\brm\s+-r\s+-f\b", re.IGNORECASE),
     "`rm -rf` recursively deletes files without confirmation; safeguard requires no -r/-f combined in the same flag group."),
    (re.compile(r"\bgit\s+push\s+(--force|-f)\b", re.IGNORECASE),
     "`git push --force` rewrites remote history; consider `--force-with-lease` instead."),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "`DROP TABLE/DATABASE/SCHEMA` is destructive and irreversible."),
    (re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z_][a-zA-Z0-9_.]*", re.IGNORECASE),
     "`TRUNCATE` clears a table without a WHERE filter."),
    (re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_.]*\s*(;|$)", re.IGNORECASE),
     "`DELETE FROM <table>` with no WHERE clause would delete every row."),
    (re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z_][a-zA-Z0-9_.]*\s+(?!WHERE|where)", re.IGNORECASE),
     "`DELETE FROM <table>` without a `WHERE` clause."),
]


def _extract_command(payload: dict) -> str:
    """Return the bash command string from a Claude Code tool-use payload."""
    # Claude Code wraps the command under tool_input.command, but be lenient.
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command")
        if isinstance(cmd, str):
            return cmd
    # Some payloads send the raw tool invocation; try top-level fields.
    for key in ("command", "cmd", "bash_command"):
        val = payload.get(key)
        if isinstance(val, str):
            return val
    return ""


def _project_path(payload: dict) -> str:
    """Best-effort project path; defaults to cwd if not provided."""
    for key in ("cwd", "project_path", "working_directory", "workspace"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val
    return os.getcwd()


def _log_block(ts: str, cmd: str, project: str, reason: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            # Single-line JSON keeps the log easy to grep/jq.
            fh.write(json.dumps({
                "ts": ts,
                "project": project,
                "command": cmd,
                "reason": reason,
            }, ensure_ascii=False) + "\n")
    except OSError:
        # Logging failures must never block — silent fail.
        pass


def _check(command: str) -> str | None:
    """Return the rule description for the first matching pattern, else None."""
    for pattern, msg in _RULES:
        if pattern.search(command):
            return msg
    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        # No payload — nothing to gate. Allow.
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Unparseable payload — be safe and allow (the upstream tool will fail
        # on its own if it's malformed).
        return 0

    if payload.get("tool_name") not in (None, "Bash"):
        # Only intercept Bash invocations.
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = _check(command)
    if not reason:
        # Clean command — allow silently with exit 0.
        return 0

    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    project = _project_path(payload)
    _log_block(ts, command, project, reason)

    # Per Anthropic's hook contract: exit 2 with stderr to block the tool call.
    sys.stderr.write(
        f"BLOCKED by safety_hook: {reason}\n"
        f"  command: {command}\n"
        f"  project: {project}\n"
        f"  logged:  {LOG_FILE}\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
