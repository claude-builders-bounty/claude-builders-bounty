#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


HOOK_EVENT = "PreToolUse"
DEFAULT_LOG = Path("~/.claude/hooks/blocked.log").expanduser()
SETTINGS_PATH = Path("~/.claude/settings.json").expanduser()


class Rule:
    def __init__(self, name: str, pattern: str, message: str):
        self.name = name
        self.pattern = re.compile(pattern, re.IGNORECASE | re.DOTALL)
        self.message = message

    def matches(self, command: str) -> bool:
        return bool(self.pattern.search(command))


RULES = [
    Rule(
        "rm -rf",
        r"\brm\s+-(?:[A-Za-z]*r[A-Za-z]*f|[A-Za-z]*f[A-Za-z]*r)\b",
        "Recursive force removal can irreversibly delete project or system files.",
    ),
    Rule(
        "DROP TABLE",
        r"\bdrop\s+table\b",
        "DROP TABLE can destroy database schema and data.",
    ),
    Rule(
        "TRUNCATE",
        r"\btruncate(?:\s+table)?\b",
        "TRUNCATE can erase table contents without row-level review.",
    ),
    Rule(
        "git push --force",
        r"\bgit\s+push\b(?=.*(?:--force(?:-with-lease)?|\s-f(?:\s|$)))",
        "Force pushing can overwrite shared remote history.",
    ),
]


def extract_command(payload: Dict[str, Any]) -> Optional[str]:
    tool_name = payload.get("tool_name") or payload.get("toolName")
    if tool_name and str(tool_name).lower() != "bash":
        return None

    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if command is None:
        command = payload.get("command")
    return str(command) if command is not None else None


def extract_project_path(payload: Dict[str, Any]) -> str:
    for key in ("project_path", "projectPath", "cwd", "workspaceFolder"):
        if payload.get(key):
            return str(payload[key])
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    if isinstance(tool_input, dict) and tool_input.get("cwd"):
        return str(tool_input["cwd"])
    return os.getcwd()


def detect_block_reason(command: str) -> Optional[str]:
    normalized = " ".join(command.split())
    for rule in RULES:
        if rule.matches(normalized):
            return f"Blocked {rule.name}: {rule.message}"

    delete_match = re.search(r"\bdelete\s+from\b", normalized, re.IGNORECASE)
    if delete_match:
        remainder = normalized[delete_match.end():]
        if not re.search(r"\bwhere\b", remainder, re.IGNORECASE):
            return (
                "Blocked DELETE FROM without WHERE: destructive SQL deletes "
                "must include an explicit WHERE clause."
            )
    return None


def log_blocked_attempt(
    *,
    command: str,
    project_path: str,
    reason: str,
    log_path: Path,
) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def deny(reason: str) -> Dict[str, Any]:
    return {
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }


def pass_through() -> Dict[str, Any]:
    return {"continue": True}


def evaluate(
    payload: Dict[str, Any],
    *,
    log_path: Optional[Path] = None,
) -> Dict[str, Any]:
    command = extract_command(payload)
    if not command:
        return pass_through()

    reason = detect_block_reason(command)
    if not reason:
        return pass_through()

    log_blocked_attempt(
        command=command,
        project_path=extract_project_path(payload),
        reason=reason,
        log_path=log_path or Path(os.environ.get("CLAUDE_HOOKS_LOG", DEFAULT_LOG)),
    )
    return deny(reason)


def install(settings_path: Path = SETTINGS_PATH) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    else:
        settings = {}

    command = "python3 ~/.claude/hooks/pre-tool-use-blocker.py"
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command}],
    }
    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])
    if entry not in pre_tool:
        pre_tool.append(entry)

    settings_path.write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Installed PreToolUse hook in {settings_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args()

    if args.install:
        install()
        return 0

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps(deny(f"Invalid hook JSON input: {exc}")))
        return 0

    print(json.dumps(evaluate(payload), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
