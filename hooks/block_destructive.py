#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks destructive bash commands."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

BLOCK_PATTERNS = [
    (re.compile(r"rm\s+(-[^\s]*\s+)*-[^\s]*r[^\s]*f|rm\s+-rf|rm\s+-fr", re.I), "rm -rf"),
    (re.compile(r"DROP\s+TABLE", re.I), "DROP TABLE"),
    (re.compile(r"git\s+push\s+.*--force|git\s+push\s+-f\b", re.I), "git push --force"),
    (re.compile(r"TRUNCATE\s+", re.I), "TRUNCATE"),
    (re.compile(r"DELETE\s+FROM\s+(?!.*\bWHERE\b)", re.I | re.S), "DELETE FROM without WHERE"),
]


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, str):
        return tool_input
    return tool_input.get("command") or tool_input.get("cmd") or json.dumps(tool_input)


def check(command: str) -> tuple[bool, str]:
    for pattern, label in BLOCK_PATTERNS:
        if pattern.search(command):
            return False, label
    return True, ""


def log_block(command: str, reason: str, project: str):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    line = f"{datetime.now(timezone.utc).isoformat()}\t{reason}\t{project}\t{command}\n"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line)


def main():
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    command = extract_command(payload)
    project = payload.get("cwd") or payload.get("project_path") or str(Path.cwd())
    ok, reason = check(command)
    if ok:
        sys.exit(0)
    log_block(command, reason, project)
    print(
        f"BLOCKED: '{reason}' detected.\n"
        f"This command was not executed to protect the project.\n"
        f"Command: {command[:200]}",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
