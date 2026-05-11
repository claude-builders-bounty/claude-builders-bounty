#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands.

The hook reads Claude Code's hook JSON from stdin. If the pending Bash command
matches a destructive pattern, it appends an audit entry to
~/.claude/hooks/blocked.log, writes a clear reason to stderr, and exits 2 so
Claude Code blocks the tool call.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DANGEROUS_SQL_PATTERNS = (
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.IGNORECASE)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.IGNORECASE)),
)

CONTROL_TOKENS = {";", "&&", "||", "|"}
WRAPPER_TOKENS = {"sudo", "command", "builtin", "time", "nohup"}


def _home() -> Path:
    return Path(os.environ.get("HOME") or Path.home()).expanduser()


def hooks_dir() -> Path:
    return _home() / ".claude" / "hooks"


def blocked_log_path() -> Path:
    return hooks_dir() / "blocked.log"


def load_hook_payload() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError as exc:
        block("Invalid Claude Code hook JSON", f"Could not parse stdin JSON: {exc}", "")
        raise AssertionError("unreachable")


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        command = tool_input.get("command")
        if isinstance(command, str):
            return command

    command = payload.get("command")
    return command if isinstance(command, str) else ""


def extract_project_path(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_path", "workspace", "transcript_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd")
        if isinstance(value, str) and value:
            return value

    return os.getcwd()


def split_shell_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def iter_command_segments(tokens: Iterable[str]) -> Iterable[list[str]]:
    current: list[str] = []
    for token in tokens:
        if token in CONTROL_TOKENS:
            if current:
                yield current
                current = []
            continue
        current.append(token)
    if current:
        yield current


def strip_wrappers(segment: list[str]) -> list[str]:
    cleaned = list(segment)
    while cleaned and cleaned[0] in WRAPPER_TOKENS:
        cleaned = cleaned[1:]
    if len(cleaned) >= 3 and cleaned[0] == "env":
        index = 1
        while index < len(cleaned) and "=" in cleaned[index] and not cleaned[index].startswith("-"):
            index += 1
        cleaned = cleaned[index:]
    return cleaned


def has_recursive_force_flag(tokens: list[str]) -> bool:
    for token in tokens:
        if not token.startswith("-"):
            continue
        if token == "--":
            return False
        normalized = token.lstrip("-")
        if "r" in normalized and "f" in normalized:
            return True
    return False


def detect_rm_rf(command: str) -> str | None:
    for segment in iter_command_segments(split_shell_tokens(command)):
        cleaned = strip_wrappers(segment)
        if not cleaned:
            continue
        if cleaned[0] == "rm" and has_recursive_force_flag(cleaned[1:]):
            return "rm -rf style recursive forced deletion"
    return None


def detect_git_force_push(command: str) -> str | None:
    for segment in iter_command_segments(split_shell_tokens(command)):
        cleaned = strip_wrappers(segment)
        if len(cleaned) < 3 or cleaned[0] != "git" or cleaned[1] != "push":
            continue
        if any(token == "--force" or token.startswith("--force-") or token == "-f" for token in cleaned[2:]):
            return "git push force flag"
    return None


def detect_delete_without_where(command: str) -> str | None:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = re.split(r";|\|\||&&|\|", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return "DELETE FROM without WHERE clause"
    return None


def detect_sql(command: str) -> str | None:
    for label, pattern in DANGEROUS_SQL_PATTERNS:
        if pattern.search(command):
            return label
    return detect_delete_without_where(command)


def find_block_reason(command: str) -> str | None:
    return detect_rm_rf(command) or detect_git_force_push(command) or detect_sql(command)


def write_block_log(reason: str, command: str, project_path: str) -> None:
    path = blocked_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "reason": reason,
        "command": command,
        "project_path": project_path,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def block(reason: str, detail: str, project_path: str) -> None:
    if detail:
        write_block_log(reason, detail, project_path)
    print(
        f"Blocked Bash command: {reason}. The command was not executed. "
        "Review it manually or rewrite it into a safer, narrower operation.",
        file=sys.stderr,
    )
    raise SystemExit(2)


def run_hook() -> int:
    payload = load_hook_payload()
    tool_name = payload.get("tool_name") or payload.get("tool")
    command = extract_command(payload)

    if tool_name not in (None, "", "Bash") or not command:
        return 0

    reason = find_block_reason(command)
    if reason:
        block(reason, command, extract_project_path(payload))
    return 0


def install() -> int:
    target_dir = hooks_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_script = target_dir / "block_destructive_bash.py"
    target_script.write_text(Path(__file__).read_text(encoding="utf-8"), encoding="utf-8")
    target_script.chmod(target_script.stat().st_mode | stat.S_IXUSR)

    settings_path = _home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            backup = settings_path.with_suffix(".json.bak")
            backup.write_text(settings_path.read_text(encoding="utf-8"), encoding="utf-8")
            settings = {}
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {target_script}"
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}
    if entry not in pre_tool_use:
        pre_tool_use.append(entry)

    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook at {target_script}")
    print(f"Updated settings at {settings_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Block destructive Claude Code Bash tool calls.")
    parser.add_argument("--install", action="store_true", help="Install into ~/.claude/hooks and update settings.json")
    args = parser.parse_args()
    if args.install:
        return install()
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
