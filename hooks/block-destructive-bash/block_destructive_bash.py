#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path


BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"
HOOK_COMMAND = "python3 ~/.claude/hooks/block_destructive_bash.py"


def load_event() -> dict:
    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return {}

    try:
        return json.loads(raw_input)
    except json.JSONDecodeError:
        return {}


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, comments=False, posix=True)
    except ValueError:
        return command.split()


def has_rm_rf(words: list[str]) -> bool:
    for index, word in enumerate(words):
        if word != "rm":
            continue

        flags = words[index + 1 :]
        has_recursive = False
        has_force = False
        for flag in flags:
            if flag == "--":
                break
            if not flag.startswith("-"):
                continue
            has_recursive = has_recursive or "r" in flag or flag in {"--recursive", "--dir"}
            has_force = has_force or "f" in flag or flag == "--force"
        if has_recursive and has_force:
            return True

    return False


def has_force_push(words: list[str]) -> bool:
    for index in range(0, max(len(words) - 2, 0)):
        if words[index : index + 2] != ["git", "push"]:
            continue

        if any(word == "-f" or word.startswith("--force") for word in words[index + 2 :]):
            return True

    return False


def delete_from_without_where(command: str) -> bool:
    for statement in re.split(r";|\n", command):
        if re.search(r"\bdelete\s+from\b", statement, flags=re.IGNORECASE):
            if not re.search(r"\bwhere\b", statement, flags=re.IGNORECASE):
                return True

    return False


def block_reason(command: str) -> str | None:
    words = shell_words(command)

    if has_rm_rf(words) or re.search(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f|\brm\s+-[A-Za-z]*f[A-Za-z]*r", command):
        return "rm -rf style recursive force deletion is blocked"

    if has_force_push(words):
        return "force-pushing with git push --force is blocked"

    if re.search(r"\bdrop\s+table\b", command, flags=re.IGNORECASE):
        return "DROP TABLE is blocked"

    if re.search(r"\btruncate\b", command, flags=re.IGNORECASE):
        return "TRUNCATE is blocked"

    if delete_from_without_where(command):
        return "DELETE FROM without a WHERE clause is blocked"

    return None


def project_path(event: dict) -> str:
    return (
        event.get("cwd")
        or event.get("project_dir")
        or event.get("workspace")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )


def log_block(event: dict, command: str, reason: str) -> None:
    BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "project_path": project_path(event),
        "reason": reason,
        "command": command,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as log_file:
        log_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def install_hook() -> int:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Refusing to overwrite invalid JSON in {SETTINGS_FILE}", file=sys.stderr)
            return 1
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    hook_entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": HOOK_COMMAND}],
    }

    if hook_entry not in pre_tool_use:
        pre_tool_use.append(hook_entry)

    SETTINGS_FILE.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed destructive Bash guard in {SETTINGS_FILE}")
    return 0


def run_hook() -> int:
    event = load_event()
    if event.get("tool_name") not in {None, "Bash"}:
        return 0

    command = event.get("tool_input", {}).get("command", "")
    if not command:
        return 0

    reason = block_reason(command)
    if not reason:
        return 0

    log_block(event, command, reason)
    print(
        f"Blocked destructive Bash command: {reason}. "
        "Use a safer command or ask the user for an explicit manual action.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash tool calls.")
    parser.add_argument("--install", action="store_true", help="Install this hook in ~/.claude/settings.json")
    args = parser.parse_args()

    if args.install:
        return install_hook()

    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
