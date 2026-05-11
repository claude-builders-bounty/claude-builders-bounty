#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


SETTINGS_SNIPPET = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python ~/.claude/hooks/block_destructive_bash.py",
                    }
                ],
            }
        ]
    }
}


def split_shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "rm":
            continue

        saw_recursive = False
        saw_force = False

        for next_token in tokens[index + 1 :]:
            if next_token in {";", "&&", "||", "|"}:
                break
            if not next_token.startswith("-") or next_token == "--":
                continue

            flag_text = next_token.lstrip("-")
            saw_recursive = saw_recursive or "r" in flag_text or "R" in flag_text
            saw_force = saw_force or "f" in flag_text

            if saw_recursive and saw_force:
                return True

    return False


def has_git_force_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if token != "git":
            continue

        subcommand_tokens = tokens[index + 1 :]
        if not subcommand_tokens:
            continue

        try:
            push_index = subcommand_tokens.index("push")
        except ValueError:
            continue

        push_args = subcommand_tokens[push_index + 1 :]
        for arg in push_args:
            if arg in {";", "&&", "||", "|"}:
                break
            if arg == "-f" or arg.startswith("--force"):
                return True

    return False


def delete_without_where(command: str) -> bool:
    for match in DELETE_FROM_RE.finditer(command):
        statement_tail = command[match.end() :]
        statement = statement_tail.split(";", 1)[0]
        if not WHERE_RE.search(statement):
            return True
    return False


def blocked_reasons(command: str) -> list[str]:
    tokens = split_shell_words(command)
    reasons = []

    if has_rm_rf(tokens):
        reasons.append("rm with recursive and force flags can delete files permanently")

    if has_git_force_push(tokens):
        reasons.append("force-pushing can rewrite shared Git history")

    if DROP_TABLE_RE.search(command):
        reasons.append("DROP TABLE can destroy database schema and data")

    if TRUNCATE_RE.search(command):
        reasons.append("TRUNCATE can remove all rows from a table")

    if delete_without_where(command):
        reasons.append("DELETE FROM without WHERE can remove all rows from a table")

    return reasons


def project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "workspace", "workspace_dir"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    env_project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_project_dir:
        return env_project_dir

    return os.getcwd()


def log_blocked(command: str, reasons: Iterable[str], path: str) -> None:
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": path,
        "reason": "; ".join(reasons),
        "command": command,
    }

    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True) + "\n")


def deny(reason: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def run_hook(stdin_text: str) -> int:
    try:
        payload = json.loads(stdin_text or "{}")
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reasons = blocked_reasons(command)
    if not reasons:
        return 0

    path = project_path(payload)
    log_blocked(command, reasons, path)
    deny("Blocked destructive Bash command: " + "; ".join(reasons))
    return 0


def run_self_test() -> int:
    cases = [
        ("npm test", False),
        ("rm file.txt", False),
        ("rm -rf build", True),
        ("rm -fr build", True),
        ("rm -r -f build", True),
        ("git push origin main", False),
        ("git push --force origin main", True),
        ("git push -f origin main", True),
        ("psql -c 'DROP TABLE users'", True),
        ("sqlite3 app.db 'TRUNCATE users'", True),
        ("sqlite3 app.db 'DELETE FROM users;'", True),
        ("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'", False),
    ]

    failures = []
    for command, expected in cases:
        actual = bool(blocked_reasons(command))
        if actual != expected:
            failures.append((command, expected, actual))

    if failures:
        for command, expected, actual in failures:
            print(
                f"FAIL: {command!r}: expected blocked={expected}, got blocked={actual}",
                file=sys.stderr,
            )
        return 1

    print(f"OK: {len(cases)} self-tests passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--print-settings", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    if args.print_settings:
        print(json.dumps(SETTINGS_SNIPPET, indent=2))
        return 0

    return run_hook(sys.stdin.read())


if __name__ == "__main__":
    raise SystemExit(main())
