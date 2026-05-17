#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

BLOCK_REASON = (
    "Blocked destructive Bash command: it matches a denylisted pattern "
    "(rm -rf, DROP TABLE, git push --force, TRUNCATE, or DELETE FROM without WHERE)."
)

SEPARATORS = {";", "&&", "||", "|"}


def _command_from_input(payload: dict) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command
    return ""


def _segment_tokens(command: str) -> list[list[str]]:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        return []

    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in SEPARATORS:
            if segments[-1]:
                segments.append([])
            continue
        segments[-1].append(token)
    return [segment for segment in segments if segment]


def _is_rm_destructive(segment: Sequence[str]) -> bool:
    for index, token in enumerate(segment):
        base = token.rsplit("/", 1)[-1].lower()
        if base != "rm":
            continue

        saw_recursive = False
        saw_force = False
        for follower in segment[index + 1 :]:
            if not follower.startswith("-"):
                break
            lower = follower.lower()
            if lower.startswith("--"):
                if lower == "--recursive":
                    saw_recursive = True
                if lower == "--force":
                    saw_force = True
            else:
                flags = lower[1:]
                if "r" in flags:
                    saw_recursive = True
                if "f" in flags:
                    saw_force = True
            if saw_recursive and saw_force:
                return True
    return False


def _is_git_force_push(segment: Sequence[str]) -> bool:
    lower = [token.lower() for token in segment]
    for index, token in enumerate(lower):
        if token.rsplit("/", 1)[-1] != "git":
            continue
        try:
            push_index = lower.index("push", index + 1)
        except ValueError:
            continue
        for follower in lower[push_index + 1 :]:
            if not follower.startswith("-"):
                continue
            if follower in {"--force", "-f"}:
                return True
    return False


def _has_sql_blocked_verb(segment: Sequence[str]) -> tuple[bool, str]:
    lowered = [token.lower() for token in segment]
    if "truncate" in lowered:
        return True, "TRUNCATE"
    if "drop" in lowered and "table" in lowered:
        return True, "DROP TABLE"
    if "delete" in lowered and "from" in lowered:
        from_index = lowered.index("from")
        if "where" not in lowered[from_index + 1 :]:
            return True, "DELETE FROM without WHERE"
    return False, ""


def detect_block_reason(command: str) -> str | None:
    if not command.strip():
        return None

    for segment in _segment_tokens(command):
        if _is_rm_destructive(segment):
            return "rm -rf"
        if _is_git_force_push(segment):
            return "git push --force"
        sql_blocked, label = _has_sql_blocked_verb(segment)
        if sql_blocked:
            return label
    return None


def _log_block(command: str, project_path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "attempted_command": command,
        "project_path": project_path,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False))
        handle.write("\n")


def _project_path_from_input(payload: dict) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    for key in ("project_path", "project_dir", "worktree_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    env_fallback = os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD")
    return env_fallback or str(Path.cwd())


def _emit_block(reason_label: str) -> None:
    message = f"{BLOCK_REASON} Triggered by: {reason_label}."
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")


def main(argv: Iterable[str] | None = None) -> int:
    del argv
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if not isinstance(payload, dict):
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = _command_from_input(payload)
    reason_label = detect_block_reason(command)
    if reason_label is None:
        return 0

    _log_block(command, _project_path_from_input(payload))
    _emit_block(reason_label)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
