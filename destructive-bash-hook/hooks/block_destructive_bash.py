#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

Reads a Claude Code hook JSON payload from stdin. If the payload is a Bash tool
call whose command matches a destructive pattern, it logs the attempt and returns
a PreToolUse deny decision. Safe commands exit 0 with no output so normal Claude
Code permission flow continues.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Iterable

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def _normalise_space(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _shell_tokens(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # If the command is syntactically incomplete, fall back to a lossy split;
        # destructive text should still be blocked conservatively.
        return command.split()


def _has_rm_rf(command: str) -> bool:
    """Return True for rm invocations whose flags include both r and f."""
    tokens = _shell_tokens(command)
    for idx, tok in enumerate(tokens):
        if tok != "rm":
            continue
        # Inspect flags immediately after rm. Stop when the first non-flag arg
        # appears. Handles rm -rf, rm -fr, rm -r -f, rm --recursive --force.
        has_recursive = False
        has_force = False
        for arg in tokens[idx + 1 :]:
            if arg == "--":
                break
            if not arg.startswith("-") or arg == "-":
                break
            if arg in ("--recursive", "--dir"):
                has_recursive = True
            if arg == "--force":
                has_force = True
            if arg.startswith("--"):
                continue
            flags = arg[1:]
            if "r" in flags or "R" in flags:
                has_recursive = True
            if "f" in flags:
                has_force = True
        if has_recursive and has_force:
            return True
    # Conservative fallback for shell constructs shlex may not model well.
    return bool(re.search(r"(?:^|[;&|`$()\s])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*|(?:--recursive|-[A-Za-z]*[rR][A-Za-z]*)\s+(?:--force|-[A-Za-z]*f[A-Za-z]*))", command))


def _has_git_push_force(command: str) -> bool:
    tokens = _shell_tokens(command)
    for i in range(len(tokens) - 2):
        if tokens[i] == "git" and tokens[i + 1] == "push":
            push_args = tokens[i + 2 :]
            return any(
                arg == "-f"
                or arg == "--force"
                or arg.startswith("--force-with-lease")
                for arg in push_args
            )
    return bool(re.search(r"\bgit\s+push\b[^\n;|&]*(?:\s-f\b|\s--force(?:\b|=)|\s--force-with-lease(?:\b|=))", command))


def _sql_statements(command: str) -> Iterable[str]:
    for part in re.split(r";|&&|\|\||\n", command):
        statement = _normalise_space(part)
        if statement:
            yield statement


def _has_dangerous_sql(command: str) -> tuple[bool, str | None]:
    upper = command.upper()
    if re.search(r"\bDROP\s+TABLE\b", upper):
        return True, "DROP TABLE is destructive"
    if re.search(r"\bTRUNCATE\b", upper):
        return True, "TRUNCATE is destructive"
    for stmt in _sql_statements(command):
        if re.search(r"\bDELETE\s+FROM\b", stmt, re.IGNORECASE) and not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
            return True, "DELETE FROM without WHERE can delete every row"
    return False, None


def classify(command: str) -> str | None:
    if _has_rm_rf(command):
        return "rm with recursive force flags can delete large directory trees"
    sql_blocked, sql_reason = _has_dangerous_sql(command)
    if sql_blocked:
        return sql_reason
    if _has_git_push_force(command):
        return "git push --force can rewrite shared history"
    return None


def _project_path(payload: dict) -> str:
    for key in ("cwd", "project_dir", "workspace", "transcript_path"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            if key == "transcript_path":
                return str(Path(val).parent)
            return val
    return os.getcwd()


def _log_block(command: str, project_path: str, reason: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    safe_command = command.replace("\n", "\\n")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"{ts}\tproject={project_path}\treason={reason}\tcommand={safe_command}\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON: {exc}", file=sys.stderr)
        return 0

    if payload.get("tool_name") != "Bash":
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    reason = classify(command)
    if not reason:
        return 0

    project_path = _project_path(payload)
    _log_block(command, project_path, reason)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {reason}.",
        }
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
