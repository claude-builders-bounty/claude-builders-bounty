#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class Violation:
    rule: str
    reason: str


def _strip_strings(text: str) -> str:
    """Replace quoted strings with whitespace while preserving statement shape."""
    result: list[str] = []
    quote: str | None = None
    escaped = False

    for char in text:
        if escaped:
            result.append(" ")
            escaped = False
            continue
        if char == "\\":
            result.append(" " if quote else char)
            escaped = bool(quote)
            continue
        if quote:
            if char == quote:
                quote = None
            result.append(" ")
            continue
        if char in {"'", '"', "`"}:
            quote = char
            result.append(" ")
            continue
        result.append(char)

    return "".join(result)


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return []


def _has_rm_recursive_force(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words):
        if word != "rm":
            continue
        flags: set[str] = set()
        for arg in words[index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            if arg in {"--recursive", "--dir"}:
                flags.add("r")
            elif arg == "--force":
                flags.add("f")
            elif arg.startswith("--"):
                continue
            else:
                flags.update(arg.lstrip("-").lower())
        if "r" in flags and "f" in flags:
            return True

    return bool(re.search(r"(^|[;&|]\s*)rm\s+-(?:[^\s;&|]*r[^\s;&|]*f|[^\s;&|]*f[^\s;&|]*r)\b", command))


def _has_force_push(command: str) -> bool:
    words = _shell_words(command)
    for index, word in enumerate(words):
        if word != "git":
            continue

        remaining = words[index + 1 :]
        while len(remaining) >= 2 and remaining[0] in {"-C", "-c"}:
            remaining = remaining[2:]
        while remaining and remaining[0].startswith("--") and remaining[0] not in {"--force", "--force-with-lease"}:
            remaining = remaining[1:]

        if not remaining or remaining[0] != "push":
            continue
        if any(arg in {"--force", "--force-with-lease", "-f"} or arg.startswith("--force-with-lease=") for arg in remaining[1:]):
            return True

    return False


def _delete_from_without_where(sqlish: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", sqlish, flags=re.IGNORECASE):
        tail = sqlish[match.end() :]
        statement = re.split(r"[;\n\r]", tail, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return True
    return False


def _sql_detection_text(command: str) -> str:
    words = _shell_words(command)
    if not words:
        return command

    starts_as_text_output = words[0] in {"echo", "printf"}
    pipes_to_database = bool(re.search(r"\|\s*(psql|mysql|sqlite3|duckdb)\b", command, flags=re.IGNORECASE))
    if starts_as_text_output and not pipes_to_database:
        return _strip_strings(command)
    return command


def find_violation(command: str) -> Violation | None:
    sqlish = _sql_detection_text(command)

    checks = [
        (
            "rm_recursive_force",
            _has_rm_recursive_force(command),
            "Blocked destructive recursive delete. Remove either recursive or force flags, or ask the user to approve the exact deletion.",
        ),
        (
            "git_force_push",
            _has_force_push(command),
            "Blocked force push. Use a normal git push or ask the user to approve rewriting remote history.",
        ),
        (
            "drop_table",
            bool(re.search(r"\bdrop\s+table\b", sqlish, flags=re.IGNORECASE)),
            "Blocked DROP TABLE. Destructive database schema changes require explicit user approval.",
        ),
        (
            "truncate",
            bool(re.search(r"\btruncate(?:\s+table)?\b", sqlish, flags=re.IGNORECASE)),
            "Blocked TRUNCATE. Destructive database table clearing requires explicit user approval.",
        ),
        (
            "delete_from_without_where",
            _delete_from_without_where(sqlish),
            "Blocked DELETE FROM without a WHERE clause. Add a WHERE clause or ask the user to approve a full-table delete.",
        ),
    ]

    for rule, matched, reason in checks:
        if matched:
            return Violation(rule=rule, reason=reason)
    return None


def _write_block_log(command: str, cwd: str, violation: Violation) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    sanitized_command = command.replace("\n", "\\n").replace("\t", "\\t")
    sanitized_cwd = cwd.replace("\n", "\\n").replace("\t", "\\t")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\tproject={sanitized_cwd}\trule={violation.rule}\tcommand={sanitized_command}\n")


def _deny(reason: str) -> None:
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(response, separators=(",", ":")))


def handle(payload: dict) -> int:
    if payload.get("tool_name") != "Bash":
        return 0

    command = payload.get("tool_input", {}).get("command", "")
    if not isinstance(command, str) or not command.strip():
        return 0

    violation = find_violation(command)
    if not violation:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    _write_block_log(command, str(cwd), violation)
    _deny(violation.reason)
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"destructive-bash-guard: invalid hook JSON: {exc}", file=sys.stderr)
        return 1

    return handle(payload)


if __name__ == "__main__":
    raise SystemExit(main())
