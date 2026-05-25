#!/usr/bin/env python3
"""Claude Code PreToolUse hook that denies destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


DENY_DECISION = "deny"
HOOK_EVENT = "PreToolUse"


def _tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


RM_RF_SEGMENT = re.compile(
    r"(^|[;&|]\s*|\bsudo\s+)rm\s+"
    r"(?=[^;&|]*(?:-[A-Za-z]*r|--recursive))"
    r"(?=[^;&|]*(?:-[A-Za-z]*f|--force))",
    re.IGNORECASE,
)


def _has_rm_rf(tokens: list[str], command: str) -> bool:
    if tokens and tokens[0] == "rm":
        has_recursive = False
        has_force = False
        for token in tokens[1:]:
            if token == "--":
                break
            if token in {"-r", "-R", "--recursive"}:
                has_recursive = True
            elif token in {"-f", "--force"}:
                has_force = True
            elif token.startswith("-") and not token.startswith("--"):
                has_recursive = has_recursive or "r" in token.lower()
                has_force = has_force or "f" in token.lower()
        return has_recursive and has_force

    return bool(RM_RF_SEGMENT.search(command))


def _delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"\bdelete\s+from\b", statement, re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, re.IGNORECASE
        ):
            return True
    return False


def destructive_reason(command: str) -> str | None:
    """Return the first matching destructive-command reason, or None."""

    stripped = command.strip()
    tokens = _tokens(stripped)
    lowered_tokens = [token.lower() for token in tokens]

    if _has_rm_rf(lowered_tokens, stripped):
        return "recursive forced removal with rm -rf"

    if lowered_tokens and lowered_tokens[0] == "git" and "push" in lowered_tokens:
        push_index = lowered_tokens.index("push")
        if any(token in {"-f", "--force", "--force-with-lease"} for token in lowered_tokens[push_index + 1 :]):
            return "force-pushing git history"

    if re.search(r"\bdrop\s+table\b", stripped, re.IGNORECASE):
        return "DROP TABLE statement"

    if re.search(r"\btruncate(?:\s+table)?\b", stripped, re.IGNORECASE):
        return "TRUNCATE statement"

    if _delete_without_where(stripped):
        return "DELETE FROM statement without a WHERE clause"

    return None


def project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "projectPath", "project_dir", "projectDir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def hook_log_dir() -> Path:
    override = os.environ.get("CLAUDE_HOOK_HOME")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks"


def append_blocked_log(command: str, project: str) -> None:
    hook_dir = hook_log_dir()
    hook_dir.mkdir(parents=True, exist_ok=True)
    timestamp = _dt.datetime.now(_dt.timezone.utc).isoformat()
    entry = {"timestamp": timestamp, "command": command, "project_path": project}
    with (hook_dir / "blocked.log").open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, sort_keys=True) + "\n")


def deny_output(reason: str) -> dict[str, Any]:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        "Review the command and ask the user before attempting a safer alternative."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": DENY_DECISION,
            "permissionDecisionReason": message,
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude hook JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = destructive_reason(command)
    if reason is None:
        return 0

    append_blocked_log(command, project_path(payload))
    print(json.dumps(deny_output(reason), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
