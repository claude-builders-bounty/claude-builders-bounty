#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _blocked_log_path() -> str:
    return os.path.join(os.path.expanduser("~"), ".claude", "hooks", "blocked.log")


def _append_blocked_log(cwd: str, command: str, reason: str) -> None:
    log_path = _blocked_log_path()
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    line = f"{_now_iso()}\t{cwd}\t{reason}\t{command}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)


def _normalize(command: str) -> str:
    return re.sub(r"\s+", " ", command.strip()).lower()


def _detect_violation(command: str) -> str | None:
    c = _normalize(command)

    if re.search(r"\brm\b", c) and (re.search(r"\b-rf\b", c) or re.search(r"\b-fr\b", c) or "rm -rf" in c):
        return "Destructive file removal (rm -rf/-fr)"

    if re.search(r"\bgit\b\s+push\b", c) and ("--force" in c or re.search(r"\s-[-\w]*f\b", c)):
        return "Force push (git push --force/-f)"

    if "drop table" in c:
        return "Destructive SQL (DROP TABLE)"
    if re.search(r"\btruncate\b", c):
        return "Destructive SQL (TRUNCATE)"

    if re.search(r"\bdelete\s+from\b", c) and " where " not in c:
        return "Potentially destructive SQL (DELETE FROM without WHERE)"

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    cwd = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not isinstance(cwd, str):
        cwd = os.getcwd()

    reason = _detect_violation(command)
    if not reason:
        return 0

    try:
        _append_blocked_log(cwd=cwd, command=command, reason=reason)
    except Exception:
        pass

    sys.stderr.write(
        "Blocked by pre-tool-use guardrail: "
        + reason
        + "\n"
        + "If intentional, run manually outside Claude Code or rewrite safer (explicit paths, add WHERE, avoid --force).\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

