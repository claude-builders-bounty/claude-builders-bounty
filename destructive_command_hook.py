#!/usr/bin/env python3
"""Claude Code PreToolUse hook for rejecting high-risk shell commands.

The hook reads one Claude Code hook event as JSON from stdin. It intentionally
does not execute, rewrite, or "repair" the command; it only returns a deny
decision and records the attempted command.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class Finding:
    rule: str
    explanation: str


def _strip_shell_comments(text: str) -> str:
    """Remove uncomplicated shell comments without changing quoted text."""
    result: list[str] = []
    quote: str | None = None
    escaped = False
    for char in text:
        if escaped:
            result.append(char)
            escaped = False
        elif char == "\\" and quote != "'":
            result.append(char)
            escaped = True
        elif quote:
            result.append(char)
            if char == quote:
                quote = None
        elif char in "'\"":
            result.append(char)
            quote = char
        elif char == "#":
            break
        else:
            result.append(char)
    return "".join(result)


def _split_shell_segments(command: str) -> list[str]:
    """Split shell command lists while ignoring operators inside quotes.

    This is intentionally not a shell parser. It only recognizes the quoting
    and escaping needed to distinguish command-list operators from literal
    characters in common Bash and PowerShell input. No input is executed.
    """
    segments: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(command):
        char = command[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote is not None:
            if char in {"\\", "`"} and quote == '"':
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "\\" or char == "`":
            escaped = True
            index += 1
            continue
        if command.startswith("&&", index) or command.startswith("||", index):
            segments.append(command[start:index])
            index += 2
            start = index
            continue
        if char in {";", "|", "\n"}:
            segments.append(command[start:index])
            index += 1
            start = index
            continue
        index += 1
    segments.append(command[start:])
    return segments


def _tokens(segment: str) -> list[str]:
    # This is deliberately a light tokenizer: command detection must remain
    # useful for Bash and PowerShell without evaluating either language.
    return re.findall(r'''(?:"(?:\\.|[^"\\])*"|'[^']*'|[^\s]+)''', segment)


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def find_destructive_command(command: str) -> Finding | None:
    """Return the first destructive rule matched, or None for safe input."""
    for raw_segment in _split_shell_segments(command):
        segment = _strip_shell_comments(raw_segment).strip()
        if not segment:
            continue
        lowered = segment.casefold()
        words = [_unquote(word) for word in _tokens(segment)]
        executable = Path(words[0]).name.casefold() if words else ""

        # Avoid false positives such as: echo "rm -rf" or Write-Output ...
        if executable in {"echo", "printf", "write-output", "write-host"}:
            continue

        if executable in {"rm", "rm.exe"}:
            flags = {word.casefold() for word in words[1:] if word.startswith("-")}
            if "-rf" in flags or ("-r" in flags and "-f" in flags) or "-rfi" in flags or "-fir" in flags:
                return Finding("rm-rf", "recursive forced deletion (rm -rf) is blocked")

        if executable in {"remove-item", "ri", "del", "erase"}:
            flags = {word.casefold() for word in words[1:] if word.startswith("-") or word.startswith("/")}
            recursive = any(flag in flags for flag in {"-recurse", "-r", "/recurse", "/r"})
            forced = any(flag in flags for flag in {"-force", "-f", "/force", "/f"})
            if recursive and forced:
                return Finding("powershell-recursive-delete", "recursive forced PowerShell deletion is blocked")

        if executable in {"git", "git.exe"} and len(words) >= 2 and words[1].casefold() == "push":
            push_args = {word.casefold() for word in words[2:]}
            if "--force" in push_args or "-f" in push_args or any(arg.startswith("--force=") for arg in push_args):
                return Finding("git-push-force", "force-pushing Git history is blocked")

        # SQL may be passed as a quoted argument (for example psql -c "...").
        # A WHERE in the same statement makes DELETE FROM acceptable here.
        if re.search(r"\bDROP\s+TABLE\b", segment, re.I):
            return Finding("drop-table", "DROP TABLE is blocked")
        if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", segment, re.I):
            return Finding("truncate", "TRUNCATE is blocked")
        delete_match = re.search(r"\bDELETE\s+FROM\b", segment, re.I)
        if delete_match:
            statement = segment[delete_match.start():]
            statement = re.split(r"[;\n]", statement, maxsplit=1)[0]
            if not re.search(r"\bWHERE\b", statement, re.I):
                return Finding("delete-without-where", "DELETE FROM without WHERE is blocked")

    return None


def _event_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input") or event.get("input") or {}
    if isinstance(tool_input, dict):
        value = tool_input.get("command", "")
    else:
        value = tool_input
    return value if isinstance(value, str) else ""


def log_block(event: dict[str, Any], command: str, finding: Finding, log_path: Path) -> None:
    project = event.get("cwd") or event.get("project_path") or os.getcwd()
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"timestamp": timestamp, "command": command, "project_path": str(project), "rule": finding.rule}, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if argv == ["--install"]:
        return install()
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        print("destructive-command-hook: invalid JSON hook input", file=sys.stderr)
        return 1
    command = _event_command(event)
    finding = find_destructive_command(command)
    if finding is None:
        return 0
    log_path = Path(os.environ.get("DESTRUCTIVE_HOOK_LOG", str(DEFAULT_LOG))).expanduser()
    try:
        log_block(event, command, finding, log_path)
    except OSError as exc:
        print(f"destructive-command-hook: blocked, but could not write log: {exc}", file=sys.stderr)
    reason = f"BLOCKED: {finding.explanation}. Review the command and use a safer, targeted operation if appropriate."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": reason}}))
    print(reason, file=sys.stderr)
    return 2


def install() -> int:
    """Install a hook entry while preserving unrelated Claude settings."""
    hook_file = Path(__file__).resolve()
    settings_path = Path.home() / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Cannot read {settings_path}: {exc}", file=sys.stderr)
        return 1
    hooks = settings.setdefault("hooks", {})
    entries = hooks.setdefault("PreToolUse", [])
    command = f'python "{hook_file}"'
    if not any(command in json.dumps(entry) for entry in entries):
        entries.append({"matcher": "Bash|PowerShell", "hooks": [{"type": "command", "command": command}]})
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Installed destructive-command-hook in {settings_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
