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


HOOK_NAME = "block_destructive_bash.py"
LOG_NAME = "blocked.log"
SHELL_COMMANDS = {"bash", "sh", "zsh", "dash", "fish"}
SEPARATORS = {";", "&&", "||", "|", "\n"}


def tokenize_shell(command: str) -> list[str]:
    """Tokenize enough shell syntax to find command names and flags."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def command_name(token: str) -> str:
    return Path(token).name.lower()


def command_segments(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SEPARATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def nested_shell_commands(tokens: list[str]) -> list[str]:
    nested: list[str] = []
    for i, token in enumerate(tokens):
        if command_name(token) not in SHELL_COMMANDS:
            continue
        try:
            c_index = next(j for j in range(i + 1, len(tokens)) if tokens[j] == "-c")
            if c_index + 1 < len(tokens):
                nested.append(tokens[c_index + 1])
        except StopIteration:
            continue
    return nested


def rm_rf_reason(segment: list[str]) -> str | None:
    for index, token in enumerate(segment):
        if command_name(token) != "rm":
            continue
        has_force = False
        has_recursive = False
        for arg in segment[index + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                continue
            if arg in {"--force"}:
                has_force = True
            if arg in {"--recursive", "--dir"}:
                has_recursive = True
            if arg.startswith("--"):
                continue
            short_flags = arg.lstrip("-")
            if "f" in short_flags:
                has_force = True
            if "r" in short_flags.lower() or "R" in short_flags:
                has_recursive = True
        if has_force and has_recursive:
            return "rm with both recursive and force flags"
    return None


def git_force_push_reason(segment: list[str]) -> str | None:
    for index, token in enumerate(segment):
        if command_name(token) != "git":
            continue
        git_args = segment[index + 1 :]
        if "push" not in git_args:
            continue
        push_index = git_args.index("push")
        push_args = git_args[push_index + 1 :]
        for arg in push_args:
            if arg in {"--force", "-f", "--force-with-lease"}:
                return f"git push force flag ({arg})"
            if arg.startswith("+"):
                return "git push force refspec"
    return None


def sql_reason(command: str) -> str | None:
    normalized = re.sub(r"\s+", " ", command).strip()
    if re.search(r"\bdrop\s+table\b", normalized, flags=re.IGNORECASE):
        return "DROP TABLE statement"
    if re.search(r"\btruncate(?:\s+table)?\b", normalized, flags=re.IGNORECASE):
        return "TRUNCATE statement"

    for match in re.finditer(r"\bdelete\s+from\b", normalized, flags=re.IGNORECASE):
        statement = normalized[match.start() :]
        semicolon = statement.find(";")
        if semicolon != -1:
            statement = statement[:semicolon]
        if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
            return "DELETE FROM statement without a WHERE clause"
    return None


def detect_block_reason(command: str, _depth: int = 0) -> str | None:
    if not command.strip():
        return None

    try:
        tokens = tokenize_shell(command)
    except ValueError:
        tokens = command.split()

    for segment in command_segments(tokens):
        reason = rm_rf_reason(segment) or git_force_push_reason(segment)
        if reason:
            return reason

    if _depth < 2:
        for nested in nested_shell_commands(tokens):
            reason = detect_block_reason(nested, _depth + 1)
            if reason:
                return reason

    return sql_reason(command)


def log_blocked_attempt(command: str, project_path: str, reason: str) -> Path:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    log_path = hooks_dir / LOG_NAME
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_path


def deny_payload(reason: str, log_path: Path) -> dict[str, Any]:
    message = (
        f"Blocked destructive Bash command: {reason}. "
        f"The attempt was logged to {log_path}."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        }
    }


def handle_hook(payload: dict[str, Any]) -> int:
    if payload.get("hook_event_name") not in {None, "PreToolUse"}:
        return 0
    if payload.get("tool_name") not in {None, "Bash"}:
        return 0

    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    reason = detect_block_reason(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or tool_input.get("cwd") or os.getcwd())
    log_path = log_blocked_attempt(command, project_path, reason)
    print(json.dumps(deny_payload(reason, log_path)))
    return 0


def load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as settings_file:
        return json.load(settings_file)


def install_hook() -> int:
    source = Path(__file__).resolve()
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    target = hooks_dir / HOOK_NAME
    if source != target:
        shutil.copy2(source, target)
    target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings = load_json_file(settings_path)
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    hook_entry = {
        "type": "command",
        "command": sys.executable,
        "args": [str(target)],
    }
    bash_group = None
    for group in pre_tool_use:
        if group.get("matcher") == "Bash":
            bash_group = group
            break
    if bash_group is None:
        bash_group = {"matcher": "Bash", "hooks": []}
        pre_tool_use.append(bash_group)

    existing = bash_group.setdefault("hooks", [])
    already_installed = any(
        str(target) in json.dumps(item, sort_keys=True) for item in existing
    )
    if not already_installed:
        existing.append(hook_entry)

    with settings_path.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, indent=2)
        settings_file.write("\n")

    print(f"Installed {target}")
    print(f"Updated {settings_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install the hook into ~/.claude/hooks and register it in settings.json.",
    )
    args = parser.parse_args()
    if args.install:
        return install_hook()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    return handle_hook(payload)


if __name__ == "__main__":
    raise SystemExit(main())
