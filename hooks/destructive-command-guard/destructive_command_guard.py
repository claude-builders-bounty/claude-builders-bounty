#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_NAME = "destructive_command_guard.py"
CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
LOG_PATH = HOOKS_DIR / "blocked.log"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"


BLOCKERS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("DROP TABLE statements can destroy schema and data.", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("TRUNCATE statements can delete all rows in a table.", re.compile(r"\btruncate\b", re.IGNORECASE)),
)


def _read_hook_input() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid hook JSON input: {exc}") from exc


def _shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=os.name != "nt")
    except ValueError:
        return command.split()


def _blocks_recursive_force_rm(command: str) -> str | None:
    words = _shell_words(command)
    if not words or words[0] != "rm":
        return None

    has_recursive = False
    has_force = False
    for word in words[1:]:
        if word == "--":
            break
        if word in {"-r", "-R", "--recursive"}:
            has_recursive = True
        if word in {"-f", "--force"}:
            has_force = True
        if word.startswith("-") and not word.startswith("--"):
            flags = set(word[1:])
            has_recursive = has_recursive or bool(flags.intersection({"r", "R"}))
            has_force = has_force or "f" in flags

    if has_recursive and has_force:
        return "rm with both recursive and force flags can delete large directory trees without confirmation."
    return None


def _blocks_force_push(command: str) -> str | None:
    words = _shell_words(command)
    if len(words) < 3 or words[0:2] != ["git", "push"]:
        return None

    force_flags = {"--force", "-f", "--force-with-lease"}
    if any(word in force_flags or word.startswith("--force=") for word in words[2:]):
        return "force-pushing can rewrite shared Git history."
    return None


def _blocks_delete_without_where(command: str) -> str | None:
    for match in re.finditer(r"\bdelete\s+from\b", command, flags=re.IGNORECASE):
        statement_tail = command[match.end() :]
        statement_tail = statement_tail.split(";", 1)[0]
        if not re.search(r"\bwhere\b", statement_tail, flags=re.IGNORECASE):
            return "DELETE FROM without a WHERE clause can remove every row in a table."
    return None


def _block_reason(command: str) -> str | None:
    for checker in (_blocks_recursive_force_rm, _blocks_force_push, _blocks_delete_without_where):
        reason = checker(command)
        if reason:
            return reason

    for reason, pattern in BLOCKERS:
        if pattern.search(command):
            return reason

    return None


def _log_block(command: str, cwd: str | None, reason: str) -> None:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": cwd or os.getcwd(),
        "command": command,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _deny_payload(reason: str) -> dict[str, Any]:
    message = (
        f"Blocked by destructive-command-guard: {reason} "
        "Choose a safer command, add constraints, or ask the user for explicit confirmation."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def run_hook() -> int:
    payload = _read_hook_input()
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = _block_reason(command)
    if not reason:
        return 0

    cwd = payload.get("cwd")
    _log_block(command, cwd if isinstance(cwd, str) else None, reason)
    print(json.dumps(_deny_payload(reason), ensure_ascii=False))
    return 0


def install_hook() -> int:
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    target = HOOKS_DIR / HOOK_NAME
    source = Path(__file__).resolve()
    if source != target.resolve():
        shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR)

    if SETTINGS_PATH.exists():
        settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {shlex.quote(str(target))}"
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}

    already_present = any(
        item.get("matcher") == "Bash"
        and any(hook.get("command") == command for hook in item.get("hooks", []))
        for item in pre_tool_use
        if isinstance(item, dict)
    )
    if not already_present:
        pre_tool_use.append(entry)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {target}")
    print(f"Updated Claude Code settings at {SETTINGS_PATH}")
    return 0


def self_test() -> int:
    allowed = [
        "rm old-file.txt",
        "git push origin feature/safe-branch",
        "DELETE FROM sessions WHERE expires_at < now();",
        "echo 'database migration docs' | cat",
    ]
    blocked = [
        "rm -rf dist",
        "rm -fr ./tmp",
        "DROP TABLE users;",
        "TRUNCATE audit_log;",
        "git push --force origin main",
        "DELETE FROM users;",
    ]

    failures: list[str] = []
    for command in allowed:
        if _block_reason(command):
            failures.append(f"should allow: {command}")
    for command in blocked:
        if not _block_reason(command):
            failures.append(f"should block: {command}")

    deny = _deny_payload("test reason")
    hook_output = deny.get("hookSpecificOutput", {})
    if hook_output.get("hookEventName") != "PreToolUse":
        failures.append("deny payload should target PreToolUse")
    if hook_output.get("permissionDecision") != "deny":
        failures.append("deny payload should deny permission")
    if "test reason" not in hook_output.get("permissionDecisionReason", ""):
        failures.append("deny payload should explain the block reason")

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("self-test passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install hook and update ~/.claude/settings.json")
    parser.add_argument("--self-test", action="store_true", help="Run built-in command classification tests")
    args = parser.parse_args()

    if args.install:
        return install_hook()
    if args.self_test:
        return self_test()
    return run_hook()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"destructive-command-guard failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
