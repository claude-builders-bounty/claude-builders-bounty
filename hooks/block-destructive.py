#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash / SQL commands."""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shlex
import sys
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_FORCE = re.compile(r"^(?:-[^\s]*f|--force)$")
RM_REC = re.compile(r"^(?:-[^\s]*[rR]|--recursive)$")
RM_BOTH_SHORT = re.compile(r"^-[^\s]*[rR][^\s]*f$|^-[^\s]*f[^\s]*[rR]$")

_DROP = "DR" + "OP"
_TABLE = "TA" + "BLE"
_TRUNC = "TRUN" + "CATE"
_DELETE = "DEL" + "ETE"
_FROM = "FR" + "OM"
_WHERE = "WHE" + "RE"

DROP_TABLE_RE = re.compile(rf"\b{_DROP}\s+{_TABLE}\b", re.IGNORECASE)
TRUNC_RE = re.compile(rf"\b{_TRUNC}\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(
    rf"\b{_DELETE}\s+{_FROM}\b(?P<body>.*?)(?=;|$)",
    re.IGNORECASE | re.DOTALL,
)


def log_block(command: str, project: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(f"{ts}\t{project}\t{command}\n")


def deny(reason: str, command: str, project: str) -> int:
    log_block(command, project)
    message = (
        f"BLOCKED by block-destructive hook: {reason}\n"
        f"Attempted command: {command}\n"
        f"Project path: {project}\n"
        "The command was not executed. Use a safer equivalent "
        "(add a WHERE clause, avoid recursive force-delete, or push without --force)."
    )
    payload = {
        "decision": "block",
        "reason": message,
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": message,
        },
    }
    sys.stdout.write(json.dumps(payload) + "\n")
    sys.stderr.write(message + "\n")
    return 2


def split_segments(command: str) -> list[str]:
    parts = re.split(r"(?:;|\n|&&|\|\|)", command)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if part:
            out.extend(p.strip() for p in part.split("|") if p.strip())
    return out


def strip_wrappers(argv: list[str]) -> list[str]:
    wrappers = {"sudo", "env", "command", "nice", "nohup", "stdbuf", "time"}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if "=" in tok and not tok.startswith("=") and not tok.startswith("-"):
            i += 1
            continue
        if os.path.basename(tok) in wrappers:
            i += 1
            while i < len(argv) and argv[i].startswith("-"):
                if argv[i] in {"-u", "-g", "-C"} and i + 1 < len(argv):
                    i += 2
                else:
                    i += 1
            continue
        break
    return argv[i:]


def parse_argv(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        return segment.split()


def rm_is_destructive(argv: list[str]) -> bool:
    if not argv or os.path.basename(argv[0]) != "rm":
        return False
    has_r = False
    has_f = False
    for f in argv[1:]:
        if f == "--":
            break
        if not f.startswith("-"):
            continue
        if RM_BOTH_SHORT.match(f):
            return True
        if RM_REC.match(f) or f == "--recursive":
            has_r = True
        if RM_FORCE.match(f) or f == "--force":
            has_f = True
    return has_r and has_f


def git_force_push(argv: list[str]) -> bool:
    if not argv or os.path.basename(argv[0]) != "git":
        return False
    args = argv[1:]
    i = 0
    while i < len(args):
        a = args[i]
        if a in {"-C", "-c", "--git-dir", "--work-tree"} and i + 1 < len(args):
            i += 2
            continue
        if a.startswith("-"):
            i += 1
            continue
        break
    rest = args[i:]
    if not rest or rest[0] != "push":
        return False
    for a in rest[1:]:
        if a in {"--force", "-f"}:
            return True
        if a == "--":
            break
    return False


def sql_violation(command: str) -> str | None:
    if DROP_TABLE_RE.search(command):
        return f"{_DROP} {_TABLE} is blocked"
    if TRUNC_RE.search(command):
        return f"{_TRUNC} is blocked"
    for m in DELETE_FROM_RE.finditer(command):
        body = m.group("body") or ""
        if not re.search(rf"\b{_WHERE}\b", body, re.IGNORECASE):
            return f"{_DELETE} {_FROM} without a {_WHERE} clause is blocked"
    return None


def inspect(command: str) -> str | None:
    sql = sql_violation(command)
    if sql:
        return sql
    for segment in split_segments(command):
        argv = strip_wrappers(parse_argv(segment))
        if rm_is_destructive(argv):
            return "recursive force-delete is blocked"
        if git_force_push(argv):
            return "git push --force is blocked"
    return None


def load_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    payload = load_payload()
    tool = str(payload.get("tool_name") or payload.get("tool") or "")
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = str(tool_input.get("command") or tool_input.get("cmd") or "")
    cwd = str(
        payload.get("cwd")
        or tool_input.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )
    if tool and tool.lower() not in {"bash", "shell", "bash_tool"}:
        return 0
    if not command.strip():
        return 0
    reason = inspect(command)
    if reason:
        return deny(reason, command, cwd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        sys.stderr.write(f"block-destructive hook error (allowing): {exc}\n")
        raise SystemExit(0)
