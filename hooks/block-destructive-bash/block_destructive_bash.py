#!/usr/bin/env python3
"""Claude Code PreToolUse hook for blocking destructive Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


SQL_DROP_TABLE_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
SQL_TRUNCATE_RE = re.compile(r"\btruncate(?:\s+table)?\s+[A-Za-z_][\w.]*", re.IGNORECASE)
SQL_DELETE_FROM_RE = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
SQL_WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


def load_payload() -> dict[str, Any]:
  try:
    return json.load(sys.stdin)
  except json.JSONDecodeError as exc:
    print(f"Block destructive Bash hook could not parse JSON input: {exc}", file=sys.stderr)
    sys.exit(1)


def split_command(command: str) -> list[str]:
  try:
    return shlex.split(command, posix=True)
  except ValueError:
    return command.split()


def statement_after(text: str, match: re.Match[str]) -> str:
  tail = text[match.end():]
  return tail.split(";", 1)[0]


def detects_delete_without_where(command: str) -> bool:
  for match in SQL_DELETE_FROM_RE.finditer(command):
    statement_tail = statement_after(command, match)
    if not SQL_WHERE_RE.search(statement_tail):
      return True
  return False


def token_lower(token: str) -> str:
  return token.lower()


def detects_rm_recursive_force(tokens: list[str]) -> bool:
  for index, token in enumerate(tokens):
    if token_lower(token) != "rm":
      continue

    flags: set[str] = set()
    for next_token in tokens[index + 1:]:
      next_token_lc = token_lower(next_token)
      if next_token == "--":
        break
      if not next_token.startswith("-") or next_token == "-":
        continue
      if next_token_lc == "--recursive":
        flags.add("r")
      elif next_token_lc == "--force":
        flags.add("f")
      elif next_token_lc.startswith("--"):
        continue
      else:
        for char in next_token_lc[1:]:
          flags.add(char)

    if "r" in flags and "f" in flags:
      return True

  return False


def detects_git_push_force(tokens: list[str]) -> bool:
  for index, token in enumerate(tokens):
    if token_lower(token) != "git":
      continue

    following = tokens[index + 1:]

    if len(following) >= 2 and token_lower(following[0]) == "-c":
      following = following[2:]

    if len(following) >= 2 and following[0] == "-C":
      following = following[2:]

    if not following or token_lower(following[0]) != "push":
      continue

    for push_token in following[1:]:
      push_token_lc = token_lower(push_token)
      if push_token == "--":
        break
      if push_token_lc in {"--force", "--force-with-lease", "-f"}:
        return True
      if push_token_lc.startswith("-") and not push_token_lc.startswith("--"):
        # Covers compact short flags such as `git push -uf origin main`.
        if "f" in push_token_lc[1:]:
          return True

  return False


def blocked_reason(command: str) -> str | None:
  tokens = split_command(command)

  if detects_rm_recursive_force(tokens):
    return "rm recursive force"
  if detects_git_push_force(tokens):
    return "git push force"
  if SQL_DROP_TABLE_RE.search(command):
    return "DROP TABLE statement"
  if SQL_TRUNCATE_RE.search(command):
    return "TRUNCATE statement"
  if detects_delete_without_where(command):
    return "DELETE FROM without WHERE"

  return None


def log_block(command: str, project_path: str, reason: str) -> None:
  LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
  entry = {
    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "attempted_command": command,
    "project_path": project_path,
    "reason": reason,
  }
  with LOG_PATH.open("a", encoding="utf-8") as handle:
    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> int:
  payload = load_payload()

  if payload.get("tool_name") != "Bash":
    return 0

  tool_input = payload.get("tool_input") or {}
  command = str(tool_input.get("command") or "")
  project_path = str(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or "")

  if not command.strip():
    return 0

  reason = blocked_reason(command)
  if not reason:
    return 0

  log_block(command, project_path, reason)
  print(
    "Blocked destructive Bash command before execution.\n"
    f"Reason: {reason}.\n"
    "Use a safer command or ask the user for an explicit alternative.",
    file=sys.stderr,
  )
  return 2


if __name__ == "__main__":
  raise SystemExit(main())
