#!/usr/bin/env python3

import datetime as _dt
import json
import os
import re
import sys
from typing import Optional, Tuple


def _iso_utc_now() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat(timespec="seconds")


def _safe_single_line(s: str, max_len: int = 4000) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\\n")
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


_RM_RF_RE = re.compile(r"(^|\s)rm\s+[^\n\r]*-(?:[^\s\n\r]*r[^\s\n\r]*f|[^\s\n\r]*f[^\s\n\r]*r)(\s|$)", re.IGNORECASE)
_GIT_PUSH_FORCE_RE = re.compile(r"(^|\s)git\s+push\b[^\n\r]*(--force|-f)(\s|$)", re.IGNORECASE)
_DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
_DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
_WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def _detect_violation(command: str) -> Optional[Tuple[str, str]]:
    """Return (rule_id, human_reason) if blocked; otherwise None."""
    if _RM_RF_RE.search(command):
        return (
            "rm-rf",
            "Blocked destructive command pattern: rm -rf",
        )

    if _GIT_PUSH_FORCE_RE.search(command):
        return (
            "git-push-force",
            "Blocked risky git command pattern: git push --force (-f)",
        )

    # SQL-like patterns (heuristic: match anywhere in command string)
    if _DROP_TABLE_RE.search(command):
        return (
            "drop-table",
            "Blocked destructive SQL pattern: DROP TABLE",
        )

    if _TRUNCATE_RE.search(command):
        return (
            "truncate",
            "Blocked destructive SQL pattern: TRUNCATE",
        )

    # DELETE FROM without a WHERE clause (best-effort heuristic)
    m = _DELETE_FROM_RE.search(command)
    if m:
        # Only look for WHERE after the first DELETE FROM (ignore earlier WHEREs)
        tail = command[m.end() :]
        if not _WHERE_RE.search(tail):
            return (
                "delete-without-where",
                "Blocked destructive SQL pattern: DELETE FROM without WHERE",
            )

    return None


def _append_block_log(project_dir: str, command: str, rule_id: str) -> None:
    log_path = os.path.expanduser("~/.claude/hooks/blocked.log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    line = json.dumps(
        {
            "ts": _iso_utc_now(),
            "project_dir": project_dir,
            "rule": rule_id,
            "command": command,
        },
        ensure_ascii=False,
    )
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line)
        f.write("\n")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # If we can't parse input, don't block tool execution.
        return 0

    if payload.get("hook_event_name") != "PreToolUse":
        return 0

    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    project_dir = payload.get("cwd")
    if not isinstance(project_dir, str) or not project_dir.strip():
        project_dir = os.getcwd()

    violation = _detect_violation(command)
    if not violation:
        return 0

    rule_id, human_reason = violation
    try:
        _append_block_log(project_dir=project_dir, command=_safe_single_line(command), rule_id=rule_id)
    except Exception:
        # Logging failure should not prevent blocking the command.
        pass

    # Return structured decision control for PreToolUse
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{human_reason}.\n"
                f"Project: {project_dir}\n"
                "If you intended a safe operation, rerun with a non-destructive alternative."
            ),
        }
    }
    sys.stdout.write(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
