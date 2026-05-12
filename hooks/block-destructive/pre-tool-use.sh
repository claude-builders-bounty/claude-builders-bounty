#!/usr/bin/env bash
set -euo pipefail

BLOCKED_LOG="${HOME}/.claude/hooks/blocked.log"
EVENT_PAYLOAD="$(cat)"

if [[ -z "${EVENT_PAYLOAD}" ]]; then
  exit 0
fi

HOOK_EVENT_PAYLOAD="${EVENT_PAYLOAD}" python3 - "$BLOCKED_LOG" <<'PY'
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

payload = json.loads(os.environ["HOOK_EVENT_PAYLOAD"])
blocked_log = Path(sys.argv[1]).expanduser()

tool_name = payload.get("tool_name", "")
if tool_name != "Bash":
    raise SystemExit(0)

tool_input = payload.get("tool_input") or {}
command = tool_input.get("command") or tool_input.get("cmd") or ""
command_normalized = " ".join(command.strip().split())
command_lower = command_normalized.lower()

project_path = (
    payload.get("cwd")
    or tool_input.get("cwd")
    or os.environ.get("CLAUDE_PROJECT_DIR")
    or os.getcwd()
)

checks = [
    (
        re.compile(r"(^|[\s;&|])rm\s+-rf(\s|$)"),
        "Blocked destructive filesystem command: rm -rf",
    ),
    (
        re.compile(r"\bdrop\s+table\b", re.IGNORECASE),
        "Blocked destructive SQL command: DROP TABLE",
    ),
    (
        re.compile(r"\btruncate\b", re.IGNORECASE),
        "Blocked destructive SQL command: TRUNCATE",
    ),
    (
        re.compile(r"\bgit\s+push\s+--force(\s|$)"),
        "Blocked destructive git command: git push --force",
    ),
]

blocked_reason = None
for pattern, reason in checks:
    if pattern.search(command_normalized):
        blocked_reason = reason
        break

delete_from = re.search(r"\bdelete\s+from\b", command_lower)
has_where = re.search(r"\bwhere\b", command_lower)
if blocked_reason is None and delete_from and not has_where:
    blocked_reason = "Blocked destructive SQL command: DELETE FROM without WHERE"

if blocked_reason is None:
    raise SystemExit(0)

blocked_log.parent.mkdir(parents=True, exist_ok=True)
timestamp = datetime.now(timezone.utc).isoformat()
with blocked_log.open("a", encoding="utf-8") as handle:
    handle.write(
        json.dumps(
            {
                "timestamp": timestamp,
                "project_path": project_path,
                "command": command_normalized,
                "reason": blocked_reason,
            },
            ensure_ascii=True,
        )
        + "\n"
    )

print(
    json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"{blocked_reason}. "
                    f"Attempted command: {command_normalized}. "
                    f"Project path: {project_path}"
                ),
            }
        },
        ensure_ascii=True,
    )
)
raise SystemExit(0)
PY
