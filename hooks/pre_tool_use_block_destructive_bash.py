#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any


HOOK_NAME = "PreToolUse"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
HOOK_INSTALL_PATH = Path.home() / ".claude" / "hooks" / Path(__file__).name
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"


class BlockedCommand(Exception):
    def __init__(self, pattern: str, reason: str) -> None:
        super().__init__(reason)
        self.pattern = pattern
        self.reason = reason


def utc_timestamp() -> str:
    return dt.datetime.now(dt.UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def token_has_flags(token: str, required: set[str]) -> bool:
    if not token.startswith("-") or token.startswith("--"):
        return False
    return required.issubset(set(token.lstrip("-")))


def blocks_rm_rf(command: str) -> bool:
    tokens = shell_tokens(command)
    separators = {";", "&&", "||", "|"}
    for index, token in enumerate(tokens):
        if token != "rm":
            continue
        flags: set[str] = set()
        for arg in tokens[index + 1 :]:
            if arg in separators:
                break
            if arg.startswith("--"):
                if arg in {"--recursive", "--force"}:
                    flags.add("r" if arg == "--recursive" else "f")
                continue
            if token_has_flags(arg, {"r"}) or token_has_flags(arg, {"f"}):
                flags.update(set(arg.lstrip("-")))
            if {"r", "f"}.issubset(flags):
                return True
    return bool(re.search(r"(^|[;&|]\s*|sudo\s+)rm\s+-(?:[^\s;&|]*r[^\s;&|]*f|[^\s;&|]*f[^\s;&|]*r)\b", command))


def blocks_git_force_push(command: str) -> bool:
    tokens = shell_tokens(command)
    for index, token in enumerate(tokens):
        if token != "git":
            continue
        remaining = tokens[index + 1 :]
        if not remaining or remaining[0] != "push":
            continue
        if any(arg == "-f" or arg.startswith("--force") for arg in remaining[1:]):
            return True
    return bool(re.search(r"\bgit\s+push\b[^\n;&|]*(?:\s-f\b|\s--force(?:\b|=|-))", command))


def is_single_text_rendering_command(command: str) -> bool:
    tokens = shell_tokens(command)
    if not tokens:
        return False
    if tokens[0] not in {"echo", "printf", "grep", "rg", "ag"}:
        return False
    return not re.search(r"[;&|]", command)


def blocks_drop_table(command: str) -> bool:
    if is_single_text_rendering_command(command):
        return False
    return bool(re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE))


def blocks_truncate(command: str) -> bool:
    if is_single_text_rendering_command(command):
        return False
    return bool(re.search(r"\btruncate(?:\s+table)?\b", command, flags=re.IGNORECASE))


def blocks_delete_without_where(command: str) -> bool:
    if is_single_text_rendering_command(command):
        return False
    for match in re.finditer(r"\bdelete\s+from\b(?P<body>[^;|&]*)", command, flags=re.IGNORECASE | re.DOTALL):
        if not re.search(r"\bwhere\b", match.group("body"), flags=re.IGNORECASE):
            return True
    return False


def analyze_command(command: str) -> None:
    checks = [
        ("rm -rf", "Recursive forced deletion can remove large parts of the filesystem."),
        ("git push --force", "Forced pushes can rewrite shared Git history."),
        ("DROP TABLE", "DROP TABLE can destroy database schema and data."),
        ("TRUNCATE", "TRUNCATE can erase all rows from a table."),
        ("DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can erase an entire table."),
    ]
    predicates = [
        blocks_rm_rf,
        blocks_git_force_push,
        blocks_drop_table,
        blocks_truncate,
        blocks_delete_without_where,
    ]
    for (pattern, reason), predicate in zip(checks, predicates, strict=True):
        if predicate(command):
            raise BlockedCommand(pattern, reason)


def read_payload(stdin: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(stdin or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def extract_command(payload: dict[str, Any]) -> str | None:
    if payload.get("tool_name") != "Bash":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    return command if isinstance(command, str) else None


def project_path(payload: dict[str, Any]) -> str:
    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return cwd
    env_project = os.environ.get("CLAUDE_PROJECT_DIR")
    return env_project or os.getcwd()


def log_blocked(command: str, payload: dict[str, Any], blocked: BlockedCommand) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": utc_timestamp(),
        "attempted_command": command,
        "command": command,
        "project_path": project_path(payload),
        "pattern": blocked.pattern,
        "reason": blocked.reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def deny_output(blocked: BlockedCommand) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_NAME,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command ({blocked.pattern}): "
                f"{blocked.reason} The attempt was logged to {LOG_PATH}."
            ),
        }
    }


def run_hook(stdin: str) -> int:
    payload = read_payload(stdin)
    if payload is None:
        return 0
    command = extract_command(payload)
    if not command:
        return 0
    try:
        analyze_command(command)
    except BlockedCommand as blocked:
        log_blocked(command, payload, blocked)
        print(json.dumps(deny_output(blocked)))
    return 0


def install_settings() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Refusing to edit invalid JSON in {SETTINGS_PATH}: {exc}", file=sys.stderr)
            return 1
        if not isinstance(settings, dict):
            print(f"Refusing to edit non-object JSON in {SETTINGS_PATH}", file=sys.stderr)
            return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {HOOK_INSTALL_PATH}"
    entry = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": command,
            }
        ],
    }
    if entry not in pre_tool_use:
        pre_tool_use.append(entry)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Installed Claude Code PreToolUse hook in {SETTINGS_PATH}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-settings", action="store_true", help="Merge this hook into ~/.claude/settings.json")
    args = parser.parse_args()
    if args.install_settings:
        return install_settings()
    return run_hook(sys.stdin.read())


if __name__ == "__main__":
    raise SystemExit(main())
