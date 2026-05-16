#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads the Claude Code hook JSON payload from stdin. If the payload describes a
Bash command matching a destructive pattern, the hook logs the attempt and emits
Claude Code's PreToolUse deny decision JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOOK_PATH = Path.home() / ".claude" / "hooks" / "block-destructive-bash.py"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
HOOK_EVENT = "PreToolUse"


class BlockReason:
    def __init__(self, pattern: str, reason: str) -> None:
        self.pattern = pattern
        self.reason = reason


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # Unbalanced quotes should not let dangerous text bypass checks.
        return command.split()


def _has_rm_recursive_force(command: str) -> bool:
    tokens = _shell_tokens(command)
    for i, token in enumerate(tokens):
        if token != "rm":
            continue
        recursive = False
        force = False
        for arg in tokens[i + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-"):
                # Options after the first path are not part of rm option parsing.
                break
            if arg in ("-r", "-R", "--recursive"):
                recursive = True
            if arg in ("-f", "--force"):
                force = True
            if re.fullmatch(r"-[A-Za-z]*", arg):
                letters = arg[1:]
                recursive = recursive or "r" in letters or "R" in letters
                force = force or "f" in letters
            if recursive and force:
                return True
    # Catch textual variants when shlex could not parse shell syntax cleanly.
    return bool(re.search(r"(?<!\w)rm\s+-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)\b", command))


def _has_git_force_push(command: str) -> bool:
    tokens = _shell_tokens(command)
    for i in range(len(tokens) - 2):
        if tokens[i : i + 2] != ["git", "push"]:
            continue
        args = tokens[i + 2 :]
        if any(arg in ("--force", "-f") or arg.startswith("--force=") for arg in args):
            return True
    return bool(re.search(r"(?<!\w)git\s+push\b[^\n;&|]*\s(?:--force(?:=\S+)?|-f)\b", command, re.I))


def _has_delete_from_without_where(sql: str) -> bool:
    statements = re.split(r";", sql)
    for statement in statements:
        match = re.search(r"\bDELETE\s+FROM\b", statement, re.I)
        if not match:
            continue
        after_delete = statement[match.end() :]
        if not re.search(r"\bWHERE\b", after_delete, re.I):
            return True
    return False


def _is_plain_output_command(command: str) -> bool:
    tokens = _shell_tokens(command)
    return bool(tokens and tokens[0] in {"echo", "printf"})


def detect_block_reason(command: str) -> BlockReason | None:
    if _has_rm_recursive_force(command):
        return BlockReason("rm -rf", "Recursive forced remove is destructive and must be reviewed by a human.")
    if _has_git_force_push(command):
        return BlockReason("git push --force", "Force-pushing can rewrite shared history.")

    # SQL is often passed to clients inside shell quotes, e.g. `psql -c 'DROP TABLE t'`.
    # Inspect the raw command so those quoted SQL statements are still blocked, but
    # avoid noisy false positives for plain output commands documenting SQL text.
    if _is_plain_output_command(command):
        return None

    if re.search(r"\bDROP\s+TABLE\b", command, re.I):
        return BlockReason("DROP TABLE", "Dropping tables can permanently destroy data.")
    if re.search(r"\bTRUNCATE\b", command, re.I):
        return BlockReason("TRUNCATE", "Truncating tables can permanently delete data.")
    if _has_delete_from_without_where(command):
        return BlockReason("DELETE FROM without WHERE", "DELETE FROM without a WHERE clause can delete every row.")
    return None


def _project_path(payload: dict[str, Any]) -> str:
    candidates = [
        os.environ.get("CLAUDE_PROJECT_DIR"),
        payload.get("cwd"),
        payload.get("project_dir"),
        payload.get("workspace"),
    ]
    for value in candidates:
        if isinstance(value, str) and value:
            return value
    return os.getcwd()


def log_blocked_attempt(command: str, project_path: str, block: BlockReason) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = {
        "timestamp": timestamp,
        "project_path": project_path,
        "pattern": block.pattern,
        "command": command,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def deny_output(block: BlockReason, project_path: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive Bash command ({block.pattern}): {block.reason} "
                f"Project: {project_path}. Logged to {LOG_PATH}."
            ),
        }
    }


def run_hook(payload: dict[str, Any]) -> int:
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not command.strip():
        return 0

    block = detect_block_reason(command)
    if block is None:
        return 0

    project_path = _project_path(payload)
    log_blocked_attempt(command, project_path, block)
    print(json.dumps(deny_output(block, project_path), ensure_ascii=False))
    return 0


def install_settings() -> int:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"Refusing to edit invalid JSON in {SETTINGS_PATH}: {exc}", file=sys.stderr)
            return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    hook_group = {
        "matcher": "Bash",
        "hooks": [
            {
                "type": "command",
                "command": str(HOOK_PATH),
            }
        ],
    }

    serialized = json.dumps(hook_group, sort_keys=True)
    if not any(json.dumps(group, sort_keys=True) == serialized for group in pre_tool_use):
        pre_tool_use.append(hook_group)

    SETTINGS_PATH.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed PreToolUse hook in {SETTINGS_PATH}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash tool calls")
    parser.add_argument("--install", action="store_true", help="merge this hook into ~/.claude/settings.json")
    args = parser.parse_args(argv)

    if args.install:
        return install_settings()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid Claude Code hook JSON: {exc}", file=sys.stderr)
        return 1
    return run_hook(payload)


if __name__ == "__main__":
    raise SystemExit(main())

