#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

BLOCK_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"

RM_RF_PATTERN = re.compile(r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\b|\brm\s+-[A-Za-z]*f[A-Za-z]*r[A-Za-z]*\b")
DROP_TABLE_PATTERN = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
GIT_FORCE_PUSH_PATTERN = re.compile(r"\bgit\s+push\b(?=.*(?:--force(?:=\S+)?|-f)\b)", re.IGNORECASE)
TRUNCATE_PATTERN = re.compile(r"\btruncate\b", re.IGNORECASE)
DELETE_FROM_PATTERN = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE_PATTERN = re.compile(r"\bwhere\b", re.IGNORECASE)


def _sql_statements(command: str) -> list[str]:
  return [statement.strip() for statement in re.split(r";|\n", command) if statement.strip()]


def evaluate_command(command: str) -> str | None:
  """Return a blocking reason, or None if the command is allowed."""
  if RM_RF_PATTERN.search(command):
    return "Refusing to run recursive forced removal (`rm -rf`)."
  if DROP_TABLE_PATTERN.search(command):
    return "Refusing to run destructive SQL (`DROP TABLE`)."
  if GIT_FORCE_PUSH_PATTERN.search(command):
    return "Refusing to run a force push (`git push --force` or `git push -f`)."
  if TRUNCATE_PATTERN.search(command):
    return "Refusing to run destructive SQL (`TRUNCATE`)."

  for statement in _sql_statements(command):
    if DELETE_FROM_PATTERN.search(statement) and not WHERE_PATTERN.search(statement):
      return "Refusing to run `DELETE FROM` without a `WHERE` clause."

  return None


def _project_path(payload: dict[str, Any]) -> str:
  cwd = payload.get("cwd")
  if isinstance(cwd, str) and cwd:
    return cwd
  project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
  if project_dir:
    return project_dir
  return os.getcwd()


def _command_from_payload(payload: dict[str, Any]) -> str:
  tool_input = payload.get("tool_input")
  if not isinstance(tool_input, dict):
    return ""
  command = tool_input.get("command")
  return command if isinstance(command, str) else ""


def _log_block(command: str, project_path: str, reason: str) -> None:
  BLOCK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
  timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
  with BLOCK_LOG_PATH.open("a", encoding="utf-8") as log_file:
    log_file.write(
      json.dumps(
        {
          "timestamp": timestamp,
          "project_path": project_path,
          "attempted_command": command,
          "reason": reason,
        },
        ensure_ascii=False,
      )
      + "\n",
    )


def _deny(reason: str, command: str, project_path: str) -> dict[str, Any]:
  message = (
    f"{reason} The attempted Bash command was blocked before execution. "
    f"Project path: {project_path}. Command: {command}"
  )
  return {
    "hookSpecificOutput": {
      "hookEventName": "PreToolUse",
      "permissionDecision": "deny",
      "permissionDecisionReason": message,
    },
  }


def main() -> int:
  try:
    payload = json.load(sys.stdin)
  except json.JSONDecodeError as error:
    print(f"destructive-bash-guard: invalid hook JSON: {error}", file=sys.stderr)
    return 0

  if payload.get("tool_name") != "Bash":
    return 0

  command = _command_from_payload(payload)
  reason = evaluate_command(command)
  if reason is None:
    return 0

  project_path = _project_path(payload)
  _log_block(command, project_path, reason)
  print(json.dumps(_deny(reason, command, project_path)))
  return 0


if __name__ == "__main__":
  raise SystemExit(main())
