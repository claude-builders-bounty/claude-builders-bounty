#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable


LOG_ENV_VAR = "CLAUDE_BLOCKED_BASH_LOG"


def _split_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def _strip_sql_comments(command: str) -> str:
    command = re.sub(r"/\*.*?\*/", " ", command, flags=re.DOTALL)
    command = re.sub(r"--[^\n\r]*", " ", command)
    return command


def _statement_chunks(command: str) -> Iterable[str]:
    for chunk in re.split(r";|&&|\|\||\|", command):
        stripped = chunk.strip()
        if stripped:
            yield stripped


def _has_recursive_force_rm(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if os.path.basename(token) != "rm":
            continue

        flags = ""
        for option in tokens[index + 1 :]:
            if option in {";", "&&", "||", "|"}:
                break
            if not option.startswith("-"):
                continue
            if option.startswith("--"):
                if option in {"--recursive", "--force"}:
                    flags += option
                continue
            flags += option.lstrip("-")

        has_recursive = "r" in flags or "--recursive" in flags
        has_force = "f" in flags or "--force" in flags
        if has_recursive and has_force:
            return True

    return False


def _has_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if os.path.basename(token) != "git":
            continue

        next_tokens = tokens[index + 1 :]
        try:
            push_index = next_tokens.index("push")
        except ValueError:
            continue

        for option in next_tokens[push_index + 1 :]:
            if option == "--force-with-lease":
                continue
            if option == "--force" or option.startswith("--force="):
                return True
            if re.fullmatch(r"-[A-Za-z]*f[A-Za-z]*", option):
                return True

    return False


def detect_block_reason(command: str) -> str | None:
    """Return a human-readable block reason, or None when command is safe."""

    tokens = _split_words(command)
    if _has_recursive_force_rm(tokens):
        return "Blocked recursive force delete (`rm -rf` / `rm -fr`) to prevent irreversible data loss."

    if _has_force_push(tokens):
        return "Blocked `git push --force` / `git push -f` to avoid rewriting shared history."

    sql = _strip_sql_comments(command)
    if re.search(r"\bdrop\s+table\b", sql, flags=re.IGNORECASE):
        return "Blocked `DROP TABLE` because it can permanently remove schema and data."

    if re.search(r"\btruncate(?:\s+table)?\b", sql, flags=re.IGNORECASE):
        return "Blocked `TRUNCATE` because it can wipe table contents without row-level filtering."

    for statement in _statement_chunks(sql):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE) and not re.search(
            r"\bwhere\b", statement, flags=re.IGNORECASE
        ):
            return "Blocked `DELETE FROM` without a `WHERE` clause to prevent full-table deletion."

    return None


def _log_path() -> Path:
    override = os.environ.get(LOG_ENV_VAR)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, reason: str) -> None:
    path = _log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.UTC).isoformat().replace("+00:00", "Z"),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, separators=(",", ":")) + "\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response, separators=(",", ":")))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_event_name") != "PreToolUse" or payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command:
        return 0

    reason = detect_block_reason(command)
    if not reason:
        return 0

    project_path = (
        str(payload.get("cwd") or "")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    log_blocked_attempt(command, project_path, reason)
    _deny(reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
