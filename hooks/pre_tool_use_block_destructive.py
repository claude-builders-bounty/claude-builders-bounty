#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash before it runs.

Reads the Claude Code hook JSON from stdin. When tool_name is Bash and the
command matches a destructive pattern, logs the attempt and exits with code 2
so Claude receives the reason on stderr and can choose a safer alternative.

Exit codes (Claude Code hooks contract):
  0  allow the tool call
  2  block the tool call; stderr is fed back to Claude
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

# Each rule: (id, human reason, compiled pattern)
# Patterns operate on the raw command string. They are intentionally explicit
# to avoid false positives on normal development commands.
RULES: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "rm_rf",
        "Recursive force delete (`rm -rf`) is blocked to prevent irreversible data loss.",
        re.compile(r"(?:^|[\s;&|`$(])rm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b"),
    ),
    (
        "drop_table",
        "SQL `DROP TABLE` is blocked (schema destruction).",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
    ),
    (
        "truncate",
        "SQL `TRUNCATE` is blocked (unrecoverable row wipe).",
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?", re.IGNORECASE),
    ),
    (
        "delete_from_no_where",
        "SQL `DELETE FROM` without a `WHERE` clause is blocked (would delete every row).",
        re.compile(
            r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "git_push_force",
        "Force push (`git push --force` / `-f`) is blocked to avoid overwriting remote history.",
        re.compile(
            r"\bgit\s+push\b(?:\s+(?:--force-with-lease|--force|-f)\b)"
            r"|(?:--force-with-lease|--force|-f)(?:\s+\S+)*\s+.*\bgit\s+push\b"
            r"|\bgit\s+push\b[^|;&]*\s(?:--force-with-lease|--force|-f)\b",
        ),
    ),
]


def _extract_command(payload: dict) -> str | None:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if isinstance(command, str):
        return command
    # Some harnesses nest the command under `arguments`
    arguments = payload.get("arguments") or {}
    command = arguments.get("command")
    return command if isinstance(command, str) else None


def _match_rule(command: str) -> tuple[str, str] | None:
    for rule_id, reason, pattern in RULES:
        if pattern.search(command):
            return rule_id, reason
    return None


def _log_attempt(payload: dict, command: str, rule_id: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cwd = payload.get("cwd") or os.getcwd()
    ts = datetime.now(timezone.utc).isoformat()
    # Single-line record: easy to grep; command kept raw (escaped newlines).
    line = "\t".join(
        [
            ts,
            rule_id,
            cwd.replace("\t", " "),
            command.replace("\r", "\\r").replace("\n", "\\n"),
            reason,
        ]
    )
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Malformed hook input: fail open so we never brick unrelated tools.
        return 0

    tool_name = payload.get("tool_name") or ""
    if tool_name and tool_name != "Bash":
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    matched = _match_rule(command)
    if not matched:
        return 0

    rule_id, reason = matched
    _log_attempt(payload, command, rule_id, reason)

    preview = command if len(command) <= 200 else command[:197] + "..."
    message = (
        f"BLOCKED by pre-tool-use hook (rule={rule_id}).\n"
        f"{reason}\n"
        f"Attempted command: {preview}\n"
        f"If this is truly required, run it yourself outside Claude Code "
        f"after explaining the risk to the user. Prefer a reversible alternative."
    )
    # Exit 2 → tool call denied; stderr is shown to Claude.
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
