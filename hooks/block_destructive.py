#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_PATH = Path(os.environ.get("CLAUDE_BLOCKED_LOG_PATH", HOOK_DIR / "blocked.log"))


@dataclass(frozen=True)
class Decision:
    blocked: bool
    reason: str = ""


def extract_command(payload: Any) -> str:
    """Extract a Bash command from common Claude Code hook payload shapes."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""

    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "bash_command", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value

    for key in ("command", "cmd", "bash_command", "script"):
        value = payload.get(key)
        if isinstance(value, str):
            return value

    return ""


def extract_project_path(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ("cwd", "project_path", "workspace", "repo_path"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value

        tool_input = payload.get("tool_input")
        if isinstance(tool_input, dict):
            value = tool_input.get("cwd")
            if isinstance(value, str) and value.strip():
                return value

    return os.getcwd()


def delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b(?P<tail>[^;]*)", command, re.IGNORECASE | re.DOTALL):
        tail = match.group("tail")
        if not re.search(r"\bwhere\b", tail, re.IGNORECASE):
            return True
    return False


def classify_command(command: str) -> Decision:
    checks = [
        (r"\brm\s+-[^\s;]*r[^\s;]*f[^\s;]*\b", "`rm -rf` style recursive force deletion"),
        (r"\brm\s+-[^\s;]*f[^\s;]*r[^\s;]*\b", "`rm -fr` style recursive force deletion"),
        (r"\bdrop\s+table\b", "`DROP TABLE` SQL statement"),
        (r"\bgit\s+push\b[^\n;]*(--force|-f\b)", "`git push --force` or `git push -f`"),
        (r"\btruncate\b", "`TRUNCATE` destructive command or SQL statement"),
    ]
    for pattern, reason in checks:
        if re.search(pattern, command, re.IGNORECASE):
            return Decision(True, reason)

    if delete_without_where(command):
        return Decision(True, "`DELETE FROM` without a `WHERE` clause")

    return Decision(False)


def log_blocked(command: str, project_path: str, reason: str, log_path: Path = LOG_PATH) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "attempted_command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_payload() -> Any:
    text = sys.stdin.read()
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def run_hook(log_path: Path = LOG_PATH) -> int:
    payload = read_payload()
    command = extract_command(payload)
    decision = classify_command(command)

    if not decision.blocked:
        return 0

    project_path = extract_project_path(payload)
    log_blocked(command, project_path, decision.reason, log_path)

    message = (
        "Blocked destructive Bash command before execution: "
        f"{decision.reason}. Review the command manually before proceeding."
    )
    print(json.dumps({"decision": "block", "reason": message}))
    print(message, file=sys.stderr)
    return 2


def install() -> None:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    target = HOOK_DIR / "block_destructive.py"
    shutil.copy2(Path(__file__), target)

    settings_path = Path.home() / ".claude" / "settings.json"
    settings = {}
    if settings_path.exists():
        settings = json.loads(settings_path.read_text(encoding="utf-8"))

    command = f"{sys.executable} {target}"
    pre_tool = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    entry = {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": command}],
    }
    if entry not in pre_tool:
        pre_tool.append(entry)

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    print(f"Installed hook to {target}")
    print(f"Updated {settings_path}")


def self_test() -> None:
    cases = {
        "echo safe": False,
        "git status --short": False,
        "rm -rf build": True,
        "rm -fr build": True,
        "git push origin main --force": True,
        "psql -c 'DROP TABLE users'": True,
        "sqlite3 app.db 'TRUNCATE audit_log'": True,
        "sqlite3 app.db 'DELETE FROM audit_log'": True,
        "sqlite3 app.db 'DELETE FROM audit_log WHERE id = 1'": False,
    }
    for command, expected in cases.items():
        actual = classify_command(command).blocked
        assert actual is expected, f"{command!r}: expected {expected}, got {actual}"

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "blocked.log"
        log_blocked("rm -rf build", "/tmp/project", "test reason", log_path)
        line = log_path.read_text(encoding="utf-8").strip()
        record = json.loads(line)
        assert record["attempted_command"] == "rm -rf build"
        assert record["project_path"] == "/tmp/project"

    print("All self-tests passed.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", action="store_true", help="Install the hook into ~/.claude/hooks and update settings.json.")
    parser.add_argument("--self-test", action="store_true", help="Run local pattern and logging tests.")
    args = parser.parse_args()

    if args.install:
        install()
        return 0
    if args.self_test:
        self_test()
        return 0
    return run_hook()


if __name__ == "__main__":
    raise SystemExit(main())
