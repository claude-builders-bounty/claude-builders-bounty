#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block destructive bash before it runs.

Install: copy this file to ~/.claude/hooks/ and register as PreToolUse for Bash
(see README.md). Exit code 2 = block (Claude Code convention for deny).

Reads JSON on stdin when available; also supports CLI:
  python block_destructive_bash.py --command "rm -rf /" --cwd /tmp
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Exit codes: 0 allow, 2 block (Claude Code pre-tool-use deny)
EXIT_ALLOW = 0
EXIT_BLOCK = 2

DEFAULT_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"

# Pattern table: (name, compiled regex on normalized command)
# DELETE FROM without WHERE is handled separately (SQL-ish).
BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "rm -rf (recursive force delete)",
        re.compile(r"(?:^|[;&|`\n]|\s)rm\s+(-[^\s]*r[^\s]*f|-rf|-fr)\b", re.I),
    ),
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.I),
    ),
    (
        "git push --force",
        re.compile(
            r"\bgit\s+push\b[^\n]*?(--force\b|-f\b)|"
            r"\bgit\s+push\s+(-f|--force)\b",
            re.I,
        ),
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\b(?:\s+TABLE)?\b", re.I),
    ),
]


def normalize_command(cmd: str) -> str:
    # Collapse whitespace so flags like `rm  -rf` still match
    return re.sub(r"\s+", " ", (cmd or "").strip())


def is_delete_without_where(cmd: str) -> bool:
    """True if command looks like DELETE FROM t without a WHERE clause."""
    # Strip strings loosely to reduce false positives from echo 'DELETE FROM x WHERE'
    s = normalize_command(cmd)
    if not re.search(r"\bDELETE\s+FROM\b", s, re.I):
        return False
    # If WHERE appears after DELETE FROM, allow
    m = re.search(r"\bDELETE\s+FROM\b(.+)$", s, re.I)
    if not m:
        return False
    rest = m.group(1)
    # Block if no WHERE before comment/semicolon end
    if re.search(r"\bWHERE\b", rest, re.I):
        return False
    return True


def find_block_reason(command: str) -> str | None:
    cmd = normalize_command(command)
    if not cmd:
        return None
    for name, pat in BLOCK_PATTERNS:
        if pat.search(cmd):
            return name
    if is_delete_without_where(cmd):
        return "DELETE FROM without WHERE"
    return None


def extract_from_stdin_payload(raw: str) -> tuple[str, str]:
    """Parse Claude Code hook JSON; return (command, cwd)."""
    raw = (raw or "").strip()
    if not raw:
        return "", os.getcwd()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Treat entire stdin as the command string
        return raw, os.getcwd()

    # Common shapes across hook versions
    tool_name = (
        data.get("tool_name")
        or data.get("toolName")
        or data.get("tool")
        or ""
    )
    tool_input = (
        data.get("tool_input")
        or data.get("toolInput")
        or data.get("input")
        or {}
    )
    if isinstance(tool_input, str):
        try:
            tool_input = json.loads(tool_input)
        except json.JSONDecodeError:
            tool_input = {"command": tool_input}

    cmd = ""
    if isinstance(tool_input, dict):
        cmd = (
            tool_input.get("command")
            or tool_input.get("cmd")
            or tool_input.get("bash")
            or ""
        )
    cwd = (
        data.get("cwd")
        or data.get("project_path")
        or (tool_input.get("cwd") if isinstance(tool_input, dict) else None)
        or os.getcwd()
    )

    # Only guard bash-like tools; allow non-bash tools through
    if tool_name and not re.search(r"bash|shell|terminal", str(tool_name), re.I):
        return "", str(cwd)

    return str(cmd), str(cwd)


def log_block(log_path: Path, command: str, cwd: str, reason: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{ts}\tproject={cwd}\treason={reason}\tcommand={command}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def block_message(reason: str, command: str) -> str:
    return (
        f"BLOCKED by pre-tool-use hook (destructive bash guard).\n"
        f"Reason: {reason}\n"
        f"Command: {command}\n"
        f"This hook blocks: rm -rf, DROP TABLE, git push --force, TRUNCATE, "
        f"and DELETE FROM without WHERE.\n"
        f"Use a safer alternative (git restore, migrations with WHERE, etc.)."
    )


def decide(command: str, cwd: str, log_path: Path | None = None) -> tuple[int, str]:
    reason = find_block_reason(command)
    if not reason:
        return EXIT_ALLOW, ""
    path = log_path or DEFAULT_LOG
    try:
        log_block(path, command, cwd, reason)
    except OSError:
        # Still block even if log disk fails
        pass
    return EXIT_BLOCK, block_message(reason, command)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    log_path = DEFAULT_LOG
    command = ""
    cwd = os.getcwd()

    # CLI overrides for tests / manual runs
    if "--command" in argv:
        i = argv.index("--command")
        command = argv[i + 1] if i + 1 < len(argv) else ""
    if "--cwd" in argv:
        i = argv.index("--cwd")
        cwd = argv[i + 1] if i + 1 < len(argv) else cwd
    if "--log" in argv:
        i = argv.index("--log")
        log_path = Path(argv[i + 1]) if i + 1 < len(argv) else log_path

    if not command:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        command, cwd_in = extract_from_stdin_payload(raw)
        if cwd_in:
            cwd = cwd_in

    code, msg = decide(command, cwd, log_path)
    if msg:
        # stderr is what Claude sees for block explanations
        print(msg, file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
