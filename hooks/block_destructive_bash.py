#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BLOCKED_LOG = Path(
    os.environ.get("CLAUDE_BLOCKED_LOG", Path.home() / ".claude" / "hooks" / "blocked.log")
)


def _normalize_command(command: str) -> str:
    return re.sub(r"\s+", " ", command).strip()


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def _has_recursive_force_rm(command: str) -> bool:
    tokens = _shell_tokens(command)

    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        seen_recursive = False
        seen_force = False
        for candidate in tokens[index + 1 :]:
            if candidate == "--":
                break
            if not candidate.startswith("-"):
                continue

            flags = candidate.lstrip("-").lower()
            if len(candidate) > 2 and candidate.startswith("--"):
                seen_recursive = seen_recursive or flags == "recursive"
                seen_force = seen_force or flags == "force"
            else:
                seen_recursive = seen_recursive or "r" in flags
                seen_force = seen_force or "f" in flags

            if seen_recursive and seen_force:
                return True

        # Fallback for shell syntax shlex does not model cleanly, such as aliases
        # or command separators adjacent to rm.
        segment = " ".join(tokens[index : index + 5])
        if re.search(r"\brm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)\b", segment):
            return True

    return False


def _has_git_force_push(command: str) -> bool:
    tokens = _shell_tokens(command)

    for index, token in enumerate(tokens):
        if token != "git":
            continue

        rest = tokens[index + 1 :]
        if not rest:
            continue

        try:
            push_index = rest.index("push")
        except ValueError:
            continue

        push_args = rest[push_index + 1 :]
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in push_args):
            return True

    return False


def _has_drop_table(command: str) -> bool:
    return bool(re.search(r"\bdrop\s+table\b", command, re.IGNORECASE))


def _has_truncate(command: str) -> bool:
    return bool(re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE))


def _delete_from_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        tail = command[match.end() :]
        statement = tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True
    return False


def classify_command(command: str) -> str | None:
    """Return a human-readable block reason, or None when command is allowed."""

    normalized = _normalize_command(command)
    if not normalized:
        return None

    checks = [
        (_has_recursive_force_rm, "rm with recursive force flags can delete large parts of the filesystem"),
        (_has_drop_table, "DROP TABLE can permanently remove database schema and data"),
        (_has_truncate, "TRUNCATE can quickly erase table contents"),
        (_delete_from_without_where, "DELETE FROM without a WHERE clause can erase an entire table"),
        (_has_git_force_push, "git push with force can overwrite remote branch history"),
    ]

    for check, reason in checks:
        if check(normalized):
            return reason

    return None


def _project_path(payload: dict[str, Any]) -> str:
    return str(
        payload.get("cwd")
        or payload.get("workspace")
        or payload.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def _log_blocked(command: str, project_path: str, reason: str) -> None:
    BLOCKED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "attempted_command": command,
        "reason": reason,
    }
    with BLOCKED_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny(reason: str) -> None:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Destructive Bash command blocked: {reason}. Rewrite the command with a safer, explicit operation.",
        }
    }
    print(json.dumps(output, ensure_ascii=False))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"block_destructive_bash.py: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = classify_command(command)

    if reason is None:
        return 0

    project_path = _project_path(payload)
    try:
        _log_blocked(command, project_path, reason)
    except OSError:
        # Blocking the dangerous command is more important than failing open if
        # the local log file cannot be written.
        pass
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
