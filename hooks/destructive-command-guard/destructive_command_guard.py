#!/usr/bin/env python3
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path


BLOCK_PATTERNS = [
    ("rm -rf", re.compile(r"(^|[;&|]\s*)rm\s+-(?:[^\s-]*r[^\s-]*f|[^\s-]*f[^\s-]*r)\b", re.I)),
    ("DROP TABLE", re.compile(r"\bdrop\s+table\b", re.I)),
    ("git push --force", re.compile(r"\bgit\s+push\b[^\n;&|]*\s(?:--force|-f)(?=\s|$)", re.I)),
    ("TRUNCATE", re.compile(r"\btruncate\b", re.I)),
    (
        "DELETE FROM without WHERE",
        re.compile(r"\bdelete\s+from\b(?:(?!\bwhere\b|;|\n).)*($|;|\n)", re.I | re.S),
    ),
]


def hook_response(decision, reason):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }


def project_path(payload):
    return (
        payload.get("cwd")
        or payload.get("workspace")
        or payload.get("project_path")
        or os.environ.get("PWD")
        or ""
    )


def blocked_reason(command):
    for label, pattern in BLOCK_PATTERNS:
        if pattern.search(command):
            return label
    return ""


def log_blocked(command, reason, path):
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    line = json.dumps(
        {
            "timestamp": timestamp,
            "reason": reason,
            "command": command,
            "project_path": path,
        },
        ensure_ascii=False,
    )
    with (log_dir / "blocked.log").open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps(hook_response("deny", "Blocked: hook received invalid JSON input.")))
        return 0

    if payload.get("tool_name") != "Bash":
        print(json.dumps(hook_response("allow", "Allowed: not a Bash tool call.")))
        return 0

    command = str(payload.get("tool_input", {}).get("command", ""))
    reason = blocked_reason(command)
    if not reason:
        print(json.dumps(hook_response("allow", "Allowed: no destructive command pattern detected.")))
        return 0

    path = project_path(payload)
    log_blocked(command, reason, path)
    print(
        json.dumps(
            hook_response(
                "deny",
                f"Blocked destructive Bash command: {reason}. Review the command and request explicit human approval before retrying.",
            )
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
