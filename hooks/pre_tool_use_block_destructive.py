#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive bash commands.

Install this file under ~/.claude/hooks/ and reference it from Claude Code's
PreToolUse hook configuration for the Bash tool. The hook reads the JSON hook
payload from stdin and exits non-zero with a structured block response when a
command matches a destructive pattern.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple

LOG_PATH = Path(os.environ.get("CLAUDE_BLOCKED_LOG", "~/.claude/hooks/blocked.log")).expanduser()


class BlockRule(NamedTuple):
    name: str
    pattern: re.Pattern[str]
    reason: str


RULES: tuple[BlockRule, ...] = (
    BlockRule(
        "rm-rf",
        re.compile(r"(^|[;&|`$()\s])rm\s+(?:[^\n;&|]*\s)?(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|--recursive\s+--force|--force\s+--recursive)\b", re.I),
        "recursive forced deletion (rm -rf) is blocked",
    ),
    BlockRule(
        "drop-table",
        re.compile(r"\bdrop\s+table\b", re.I),
        "DROP TABLE statements are blocked",
    ),
    BlockRule(
        "git-push-force",
        re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease)?\b|-f\b)", re.I),
        "forced git pushes are blocked",
    ),
    BlockRule(
        "truncate",
        re.compile(r"\btruncate\b", re.I),
        "TRUNCATE statements are blocked",
    ),
    BlockRule(
        "delete-without-where",
        re.compile(r"\bdelete\s+from\b(?![^;\n]*\bwhere\b)", re.I),
        "DELETE FROM without a WHERE clause is blocked",
    ),
)


def _walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)


def extract_command(payload: dict[str, Any]) -> str:
    """Return the Bash command from a Claude Code hook payload."""
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "bash_command", "script"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value

    # Fallback for alternate/older hook payload shapes used in tests or wrappers.
    for value in _walk_strings(payload):
        if value.strip():
            return value
    return ""


def detect_block(command: str) -> BlockRule | None:
    normalized = command.replace("\\\n", " ")
    for rule in RULES:
        if rule.pattern.search(normalized):
            return rule
    return None


def log_block(command: str, rule: BlockRule) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "command": command,
        "reason": rule.reason,
        "rule": rule.name,
    }
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def response(decision: str, reason: str | None = None) -> str:
    data: dict[str, str] = {"decision": decision}
    if reason:
        data["reason"] = reason
    return json.dumps(data, ensure_ascii=False)


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(response("block", f"Invalid hook JSON payload: {exc}"))
        return 2

    command = extract_command(payload)
    rule = detect_block(command)
    if rule is None:
        print(response("approve"))
        return 0

    log_block(command, rule)
    print(response("block", rule.reason))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
