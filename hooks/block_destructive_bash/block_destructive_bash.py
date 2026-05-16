#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
COMMAND_SEPARATORS = {";", "&&", "||", "|", "&"}
COMMAND_WRAPPERS = {"sudo", "command", "builtin"}


@dataclass(frozen=True)
class BlockDecision:
    blocked: bool
    rule: str = ""
    reason: str = ""


def shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in COMMAND_SEPARATORS:
            if current:
                segments.append(current)
                current = []
        else:
            current.append(token)
    if current:
        segments.append(current)
    return segments


def strip_wrappers(segment: list[str]) -> list[str]:
    remaining = list(segment)
    while remaining:
        command = Path(remaining[0]).name
        if command in COMMAND_WRAPPERS:
            remaining = remaining[1:]
            continue
        if command == "env":
            remaining = remaining[1:]
            while remaining and "=" in remaining[0] and not remaining[0].startswith("-"):
                remaining = remaining[1:]
            continue
        if "=" in remaining[0] and not remaining[0].startswith("-"):
            remaining = remaining[1:]
            continue
        break
    return remaining


def short_flag_contains(token: str, flag: str) -> bool:
    return token.startswith("-") and not token.startswith("--") and flag in token[1:]


def has_rm_rf(segment: list[str]) -> bool:
    command = strip_wrappers(segment)
    if not command or Path(command[0]).name != "rm":
        return False

    has_recursive = False
    has_force = False
    for token in command[1:]:
        if token == "--":
            break
        if token in {"--recursive", "-R"} or short_flag_contains(token, "r"):
            has_recursive = True
        if token == "--force" or short_flag_contains(token, "f"):
            has_force = True
    return has_recursive and has_force


def has_git_force_push(segment: list[str]) -> bool:
    command = strip_wrappers(segment)
    if not command or Path(command[0]).name != "git":
        return False

    try:
        push_index = command.index("push", 1)
    except ValueError:
        return False

    force_flags = {"--force", "-f", "--force-with-lease"}
    return any(
        token in force_flags or token.startswith("--force-with-lease=")
        for token in command[push_index + 1 :]
    )


def has_delete_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE) and not re.search(
            r"\bWHERE\b",
            statement,
            re.IGNORECASE,
        ):
            return True
    return False


def classify_command(command: str) -> BlockDecision:
    tokens = shell_tokens(command)
    for segment in command_segments(tokens):
        if has_rm_rf(segment):
            return BlockDecision(True, "rm-rf", "rm with recursive and force flags is blocked")
        if has_git_force_push(segment):
            return BlockDecision(True, "git-force-push", "force-pushing Git history is blocked")

    if re.search(r"\bDROP\s+TABLE\b", command, re.IGNORECASE):
        return BlockDecision(True, "drop-table", "DROP TABLE statements are blocked")
    if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", command, re.IGNORECASE):
        return BlockDecision(True, "truncate", "TRUNCATE statements are blocked")
    if has_delete_without_where(command):
        return BlockDecision(True, "delete-without-where", "DELETE FROM without a WHERE clause is blocked")

    return BlockDecision(False)


def log_blocked_attempt(
    command: str,
    project_path: str,
    decision: BlockDecision,
    log_path: Path = DEFAULT_LOG_PATH,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "rule": decision.rule,
        "reason": decision.reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, sort_keys=True) + "\n")


def deny_output(decision: BlockDecision) -> dict[str, object]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {decision.reason}.",
        }
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    if not command:
        return 0

    decision = classify_command(command)
    if not decision.blocked:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    log_blocked_attempt(command, project_path, decision)
    print(json.dumps(deny_output(decision)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
