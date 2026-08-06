#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive shell/database commands.

AI-assisted deliverable for:
https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

The hook reads the JSON payload Claude Code sends on stdin. It emits a
PreToolUse permissionDecision only when a configured destructive pattern is
found. For an ordinary command it exits successfully without writing stdout,
so normal Claude Code permission handling remains in control.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_EVENT = "PreToolUse"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RE = re.compile(
    r"(?im)(?:^|[;&|]\s*|\b(?:sudo|env)\s+)\s*rm\s+"
    r"(?P<flags>(?:--?[A-Za-z0-9-]+\s*)+)"
)
GIT_PUSH_RE = re.compile(
    r"(?im)(?:^|[;&|]\s*)(?:sudo\s+)?\s*git\s+push\b"
    r"(?P<rest>[^;&|\n]*(?:[;&|]|\n|$))"
)
DROP_TABLE_RE = re.compile(r"(?i)\bdrop\s+table\b")
TRUNCATE_RE = re.compile(r"(?i)\btruncate\b")
DELETE_FROM_RE = re.compile(r"(?is)\bdelete\s+from\b(?P<body>[^;]*)")
WHERE_RE = re.compile(r"(?i)\bwhere\b")


def _rm_is_recursive_force(flags_text: str) -> bool:
    flags = flags_text.split()
    has_recursive = any(
        flag in {"-r", "-R", "--recursive"} or flag.startswith("-") and "r" in flag[1:]
        for flag in flags
    )
    has_force = any(
        flag in {"-f", "--force"} or flag.startswith("-") and "f" in flag[1:]
        for flag in flags
    )
    return has_recursive and has_force


def find_reasons(command: str) -> list[str]:
    reasons: list[str] = []

    for match in RM_RE.finditer(command):
        if _rm_is_recursive_force(match.group("flags")):
            reasons.append("rm recursive+force")
            break

    for match in GIT_PUSH_RE.finditer(command):
        rest = match.group("rest")
        if re.search(r"(?i)(?<!\w)--force(?:-with-lease)?(?!\w)", rest) or re.search(
            r"(?<!\w)-f(?!\w)", rest
        ):
            reasons.append("forced git push")
            break

    if DROP_TABLE_RE.search(command):
        reasons.append("DROP TABLE")
    if TRUNCATE_RE.search(command):
        reasons.append("TRUNCATE")

    for match in DELETE_FROM_RE.finditer(command):
        if not WHERE_RE.search(match.group("body")):
            reasons.append("DELETE FROM without WHERE")
            break

    # Preserve order while removing duplicate reason labels.
    return list(dict.fromkeys(reasons))


def _read_payload() -> dict[str, Any] | None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_log(payload: dict[str, Any], command: str, reasons: list[str]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "attempted_command": command,
        "project_path": str(payload.get("cwd") or os.getcwd()),
        "reasons": reasons,
    }
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny(reasons: list[str]) -> None:
    reason_text = ", ".join(reasons)
    output = {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Blocked destructive command (" + reason_text + "). "
                "Review the command, narrow its scope, and ask the user "
                "before performing any irreversible operation."
            ),
        }
    }
    json.dump(output, sys.stdout)
    sys.stdout.write("\n")


def main() -> int:
    payload = _read_payload()
    if payload is None:
        # A malformed hook payload is a configuration error. Avoid blocking
        # every tool call; the user can diagnose it from Claude Code logs.
        return 0

    tool_name = payload.get("tool_name")
    if tool_name not in {"Bash", "PowerShell"}:
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reasons = find_reasons(command)
    if not reasons:
        return 0

    try:
        _write_log(payload, command, reasons)
    except OSError as exc:
        # Do not fail open if the audit log cannot be written. Exit code 2 is
        # a blocking PreToolUse error and stderr is shown to Claude Code.
        print(
            "Blocked destructive command, but the audit log could not be "
            f"written: {exc}",
            file=sys.stderr,
        )
        return 2
    _deny(reasons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
