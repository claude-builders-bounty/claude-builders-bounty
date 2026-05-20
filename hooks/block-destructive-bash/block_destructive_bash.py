#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_NAME = "block_destructive_bash.py"
HOOK_COMMAND = f"python3 ~/.claude/hooks/{HOOK_NAME}"


def tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def shell_words(command: str) -> list[str]:
    # Split common command separators so "cd app && rm -rf dist" is inspected.
    parts = re.split(r"(?:&&|\|\||;|\n)", command)
    words: list[str] = []
    for part in parts:
        words.extend(tokenize(part))
    return words


def command_basename(token: str) -> str:
    return Path(token).name.lower()


def has_rm_rf(command: str) -> bool:
    words = shell_words(command)
    for index, token in enumerate(words):
        if command_basename(token) != "rm":
            continue

        has_recursive = False
        has_force = False

        for option in words[index + 1 :]:
            if option == "--":
                continue
            if not option.startswith("-") or option == "-":
                break

            if option == "--recursive":
                has_recursive = True
            elif option == "--force":
                has_force = True
            elif option.startswith("--"):
                continue
            else:
                flags = option.lstrip("-")
                has_recursive = has_recursive or "r" in flags or "R" in flags
                has_force = has_force or "f" in flags

            if has_recursive and has_force:
                return True

    return False


def has_git_push_force(command: str) -> bool:
    words = shell_words(command)
    for index, token in enumerate(words):
        if command_basename(token) != "git":
            continue

        following = [word.lower() for word in words[index + 1 : index + 8]]
        if "push" not in following:
            continue

        push_index = following.index("push")
        push_args = following[push_index + 1 :]
        if any(arg in {"--force", "--force-with-lease", "-f"} for arg in push_args):
            return True

    return False


def has_drop_table(command: str) -> bool:
    return re.search(r"\bdrop\s+table\b", command, re.IGNORECASE) is not None


def has_truncate(command: str) -> bool:
    return re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE) is not None


def has_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = statement.split(";", 1)[0]
        if re.search(r"\bwhere\b", statement, re.IGNORECASE) is None:
            return True
    return False


def find_block_reason(command: str) -> str | None:
    checks = [
        (has_rm_rf, "rm with recursive and force flags can delete large directory trees"),
        (has_drop_table, "DROP TABLE can permanently remove database tables"),
        (has_git_push_force, "git push with force can overwrite shared history"),
        (has_truncate, "TRUNCATE can remove all rows from a table"),
        (has_delete_without_where, "DELETE FROM without a WHERE clause can remove all rows"),
    ]

    for check, reason in checks:
        if check(command):
            return reason
    return None


def blocked_log_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command: str, cwd: str, reason: str) -> None:
    path = blocked_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "reason": reason,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny(reason: str, command: str, cwd: str) -> int:
    log_blocked(command, cwd, reason)
    message = (
        f"Destructive Bash command blocked: {reason}. "
        "Choose a safer command, add a protective WHERE clause, or ask the user "
        "for explicit approval before continuing."
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }
    print(json.dumps(output))
    return 0


def handle_hook(payload: dict[str, Any]) -> int:
    if payload.get("hook_event_name") != "PreToolUse":
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return 0

    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = find_block_reason(command)
    if reason is None:
        return 0

    cwd = str(payload.get("cwd") or os.getcwd())
    return deny(reason, command, cwd)


def load_stdin_payload() -> dict[str, Any]:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid hook JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise SystemExit("Invalid hook JSON: expected an object")
    return data


def install() -> int:
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    target = hook_dir / HOOK_NAME
    shutil.copy2(Path(__file__), target)
    target.chmod(0o755)

    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Cannot parse {settings_path}: {exc}") from exc
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    bash_entry = None
    for entry in pre_tool_use:
        if isinstance(entry, dict) and entry.get("matcher") == "Bash":
            bash_entry = entry
            break

    if bash_entry is None:
        bash_entry = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_entry)

    bash_hooks = bash_entry.setdefault("hooks", [])
    already_installed = any(
        isinstance(item, dict)
        and item.get("type") == "command"
        and item.get("command") == HOOK_COMMAND
        for item in bash_hooks
    )
    if not already_installed:
        bash_hooks.append({"type": "command", "command": HOOK_COMMAND})

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed {target} and registered PreToolUse Bash hook in {settings_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash tool calls.")
    parser.add_argument("--install", action="store_true", help="Install the hook into ~/.claude/hooks")
    args = parser.parse_args()

    if args.install:
        return install()

    return handle_hook(load_stdin_payload())


if __name__ == "__main__":
    raise SystemExit(main())
