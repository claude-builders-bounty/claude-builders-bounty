#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class RuleMatch:
    rule: str
    reason: str


RM_RF_RE = re.compile(r"(?<![\w.-])rm\s+(?:-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*|-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*)(?:\s|$)")
DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
GIT_FORCE_PUSH_RE = re.compile(r"(?<![\w.-])git\s+push\b(?:(?![;&|]).)*(?:\s--force(?:\s|$|=)|\s-f(?:\s|$))", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def main() -> int:
    event = read_event()
    if event.get("tool_name") != "Bash":
        return 0

    command = str(event.get("tool_input", {}).get("command", ""))
    project_path = project_path_from_event(event)
    match = detect_dangerous_command(command)
    if not match:
        return 0

    write_log(command, project_path, match)
    print(json.dumps(deny_response(match), ensure_ascii=False))
    return 0


def read_event() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def project_path_from_event(event: dict) -> str:
    for key in ("cwd", "project_dir", "workspace_dir", "transcript_path"):
        value = event.get(key)
        if isinstance(value, str) and value:
            if key == "transcript_path":
                return str(Path(value).parent)
            return value
    return os.getcwd()


def detect_dangerous_command(command: str) -> RuleMatch | None:
    normalized = " ".join(command.split())
    if RM_RF_RE.search(normalized):
        return RuleMatch("rm-rf", "rm with recursive force flags can delete files irreversibly")
    if DROP_TABLE_RE.search(normalized):
        return RuleMatch("drop-table", "DROP TABLE can destroy database schema/data")
    if GIT_FORCE_PUSH_RE.search(normalized):
        return RuleMatch("git-force-push", "git push --force can rewrite shared history")
    if TRUNCATE_RE.search(normalized):
        return RuleMatch("truncate", "TRUNCATE can remove all rows from a table")
    if delete_from_without_where(normalized):
        return RuleMatch("delete-from-without-where", "DELETE FROM without WHERE can remove all rows")
    return None


def delete_from_without_where(command: str) -> bool:
    statements = re.split(r";|&&|\|\|", command)
    for statement in statements:
        if DELETE_FROM_RE.search(statement) and not WHERE_RE.search(statement):
            return True
    return False


def write_log(command: str, project_path: str, match: RuleMatch) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": project_path,
        "attempted_command": command,
        "rule": match.rule,
        "reason": match.reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny_response(match: RuleMatch) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"Blocked destructive Bash command: {match.reason}",
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())
