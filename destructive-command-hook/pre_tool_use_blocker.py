#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands.

Install this file under ~/.claude/hooks/ and configure it for PreToolUse Bash
calls. It reads the hook payload from stdin, inspects the attempted command,
logs blocked attempts, and exits non-zero only when a dangerous pattern is found.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCKERS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "rm -rf",
        re.compile(r"(?i)(?:^|[;&|\s])rm\s+-[^\n;|&]*r[^\n;|&]*f\b"),
        "Recursive forced deletion can remove project or system files.",
    ),
    (
        "DROP TABLE",
        re.compile(r"(?is)\bdrop\s+table\b"),
        "DROP TABLE can destroy database schema and data.",
    ),
    (
        "TRUNCATE",
        re.compile(r"(?is)\btruncate\b"),
        "TRUNCATE can irreversibly empty tables.",
    ),
    (
        "git push --force",
        re.compile(r"(?i)\bgit\s+push\b[^\n;|&]*(?:--force(?:-with-lease)?\b|\s-f\b)"),
        "Force pushing can rewrite shared history.",
    ),
)


def _load_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"tool_input": {"command": raw}}
    return data if isinstance(data, dict) else {}


def _nested_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _nested_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _nested_values(nested)


def _extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script", "bash", "shell", "input"):
            value = tool_input.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    values = [v for v in _nested_values(tool_input) if v.strip()]
    return "
".join(values).strip()


def _is_bash_payload(payload: dict[str, Any]) -> bool:
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "").lower()
    if not tool_name:
        return True
    return tool_name in {"bash", "shell", "terminal"} or "bash" in tool_name


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        normalized = " ".join(statement.split()).lower()
        if re.search(r"\bdelete\s+from\b", normalized) and " where " not in f" {normalized} ":
            return True
    return False


def _blocked_reason(command: str) -> str | None:
    for label, pattern, reason in BLOCKERS:
        if pattern.search(command):
            return f"Blocked pattern: {label}. {reason}"
    if _delete_without_where(command):
        return "Blocked pattern: DELETE FROM without WHERE. Add a WHERE clause or run the command manually after review."
    return None


def _project_path(payload: dict[str, Any]) -> str:
    candidates = (
        payload.get("cwd"),
        payload.get("project_path"),
        payload.get("workspace"),
        os.environ.get("PWD"),
        os.getcwd(),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return "unknown"


def _log_block(command: str, reason: str, project_path: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    safe_command = command.replace("
", "\n")
    line = f"{timestamp}	project={project_path}	reason={reason}	command={safe_command}
"
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line)


def _run_self_test() -> int:
    cases = {
        "echo ok": False,
        "git status && npm test": False,
        "rm -rf dist": True,
        "git push --force origin main": True,
        "DROP TABLE users;": True,
        "TRUNCATE audit_log;": True,
        "DELETE FROM sessions": True,
        "DELETE FROM sessions WHERE expires_at < now()": False,
    }
    failures: list[str] = []
    for command, expected in cases.items():
        actual = _blocked_reason(command) is not None
        if actual != expected:
            failures.append(f"{command!r}: expected {expected}, got {actual}")
    if failures:
        print("Self-test failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("Self-test passed: destructive patterns blocked, normal commands allowed.")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return _run_self_test()

    payload = _load_payload()
    if not _is_bash_payload(payload):
        return 0

    command = _extract_command(payload)
    if not command:
        return 0

    reason = _blocked_reason(command)
    if reason is None:
        return 0

    project = _project_path(payload)
    _log_block(command, reason, project)
    print(
        "Claude Code safety hook blocked this Bash command. "
        f"{reason} Project: {project}. "
        f"Attempt logged to {LOG_PATH}.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
