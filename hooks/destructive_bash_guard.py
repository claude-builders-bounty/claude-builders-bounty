#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class BlockReason:
    rule: str
    message: str


def _normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip())


def _has_rm_rf(command: str) -> bool:
    return bool(
        re.search(
            r"(?is)(^|[;&|()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|(?:--recursive|--force)\s+(?:--force|--recursive))\b",
            command,
        )
    )


def _has_force_push(command: str) -> bool:
    return bool(re.search(r"(?is)(^|[;&|()\s])git\s+push\b[^\n;|&]*?(?:--force(?:-with-lease)?\b|-f\b)", command))


def _has_drop_table(command: str) -> bool:
    return bool(re.search(r"(?is)\bdrop\s+table\b", command))


def _has_truncate(command: str) -> bool:
    return bool(re.search(r"(?is)\btruncate(?:\s+table)?\b", command))


def _delete_from_without_where(command: str) -> bool:
    for match in re.finditer(r"(?is)\bdelete\s+from\b", command):
        statement = command[match.start() :]
        statement = re.split(r"[;\n]|&&|\|\|", statement, maxsplit=1)[0]
        if not re.search(r"(?is)\bwhere\b", statement):
            return True
    return False


def validate_command(command: str) -> list[BlockReason]:
    checks = [
        ("rm -rf", _has_rm_rf, "Blocked `rm -rf`: recursive force removal is destructive."),
        ("git push --force", _has_force_push, "Blocked force push: rewrite-history pushes require explicit human approval."),
        ("DROP TABLE", _has_drop_table, "Blocked `DROP TABLE`: schema destruction requires explicit human approval."),
        ("TRUNCATE", _has_truncate, "Blocked `TRUNCATE`: bulk table deletion requires explicit human approval."),
        (
            "DELETE FROM without WHERE",
            _delete_from_without_where,
            "Blocked `DELETE FROM` without `WHERE`: this can delete every row in a table.",
        ),
    ]

    return [BlockReason(rule, message) for rule, check, message in checks if check(command)]


def log_blocked_attempt(command: str, project_path: str, reasons: list[BlockReason]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    reason_text = ", ".join(reason.rule for reason in reasons)
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp}\t{project_path}\t{reason_text}\t{safe_command}\n")


def deny(reasons: list[BlockReason]) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": " ".join(reason.message for reason in reasons),
                }
            },
            ensure_ascii=False,
        )
    )


def main() -> int:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        return 1

    if hook_input.get("tool_name") != "Bash":
        return 0

    command = str(hook_input.get("tool_input", {}).get("command", ""))
    if not command:
        return 0

    normalized_command = _normalize(command)
    reasons = validate_command(normalized_command)
    if not reasons:
        return 0

    project_path = str(hook_input.get("cwd") or hook_input.get("project_dir") or os.getcwd())
    log_blocked_attempt(command=normalized_command, project_path=project_path, reasons=reasons)
    deny(reasons)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
