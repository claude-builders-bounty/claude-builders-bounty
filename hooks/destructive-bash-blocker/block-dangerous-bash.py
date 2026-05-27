#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
from typing import Iterable


BLOCK_LOG = Path.home() / ".claude" / "hooks" / "blocked.log"
SAFE_TEXT_COMMANDS = {"echo", "printf"}
DB_CLIENT_HINTS = {
      "mysql",
      "mariadb",
      "psql",
      "sqlite3",
      "sqlcmd",
      "duckdb",
}
WRAPPER_COMMANDS = {"sudo", "doas", "command", "builtin"}
SUDO_OPTIONS_WITH_VALUE = {
      "-C",
      "-D",
      "-g",
      "-h",
      "-p",
      "-R",
      "-r",
      "-T",
      "-t",
      "-U",
      "-u",
      "--chdir",
      "--group",
      "--host",
      "--prompt",
      "--role",
      "--user",
}
GIT_OPTIONS_WITH_VALUE = {
      "-C",
      "-c",
      "--exec-path",
      "--git-dir",
      "--namespace",
      "--super-prefix",
      "--work-tree",
}


class Violation:
      def __init__(self, rule: str, reason: str) -> None:
                self.rule = rule
                self.reason = reason


def shell_segments(command: str) -> Iterable[str]:
      """Split enough shell syntax to inspect independent command segments."""
      for segment in re.split(r"(?:&&|\|\||;|\n|\|)", command):
                stripped = segment.strip()
                if stripped:
                              yield stripped


  def parse_tokens(segment: str) -> list[str]:
        try:
                  return shlex.split(segment, posix=True)
except ValueError:
        return segment.split()


def command_name(token: str) -> str:
      return Path(token).name.lower()


def strip_env_assignments(tokens: list[str]) -> list[str]:
      index = 0
      while index < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[index]):
                index += 1
            return tokens[index:]


def skip_options(tokens: list[str], options_with_value: set[str]) -> list[str]:
      index = 0
    while index < len(tokens):
              token = tokens[index]
              if token == "--":
                            index += 1
                            break
                        if not token.startswith("-") or token == "-":
                                      break
                                  option = token.split("=", 1)[0]
        index += 1
        if option in options_with_value and "=" not in token and index < len(tokens):
                      index += 1
              return tokens[index:]


def effective_tokens(tokens: list[str]) -> list[str]:
      tokens = strip_env_assignments(tokens)

    while tokens and command_name(tokens[0]) in WRAPPER_COMMANDS:
              tokens = skip_options(tokens[1:], SUDO_OPTIONS_WITH_VALUE)
        tokens = strip_env_assignments(tokens)

    if tokens and command_name(tokens[0]) == "env":
              tokens = skip_options(tokens[1:], set())
        tokens = strip_env_assignments(tokens)

    return tokens


def has_rm_force_recursive(tokens: list[str]) -> bool:
      tokens = effective_tokens(tokens)
    if not tokens or command_name(tokens[0]) != "rm":
              return False

    saw_recursive = False
    saw_force = False

    for token in tokens[1:]:
              if token == "--":
                            break
                        if not token.startswith("-"):
                                      continue
                                  if token in {"-r", "-R", "--recursive"}:
                                                saw_recursive = True
                                            if token in {"-f", "--force"}:
                                                          saw_force = True
                                                      if token.startswith("-") and not token.startswith("--"):
                                                                    flags = token[1:]
                                                                    saw_recursive = saw_recursive or "r" in flags or "R" in flags
                                                                    saw_force = saw_force or "f" in flags

    return saw_recursive and saw_force


def has_forced_git_push(tokens: list[str]) -> bool:
      tokens = effective_tokens(tokens)
    if len(tokens) < 3 or command_name(tokens[0]) != "git":
              return False

    rest = skip_options(tokens[1:], GIT_OPTIONS_WITH_VALUE)
    if not rest or rest[0] != "push":
              return False

    for token in rest[1:]:
              if token in {"--force", "-f", "--force-with-lease"}:
                            return True
                        if token.startswith("+"):
                                      return True
                              return False


def is_plain_text_output(command: str) -> bool:
      if re.search(r"[|<>`$()]", command):
                return False

    segments = list(shell_segments(command))
    if len(segments) != 1:
              return False

    tokens = parse_tokens(segments[0])
    return bool(tokens) and command_name(tokens[0]) in SAFE_TEXT_COMMANDS


def looks_like_sql_execution(command: str) -> bool:
      lowered = command.lower()
    if any(re.search(rf"\b{re.escape(client)}\b", lowered) for client in DB_CLIENT_HINTS):
              return True
    if re.search(r"\b(drop\s+table|truncate(?:\s+table)?|delete\s+from)\b", lowered):
              return not is_plain_text_output(command)
    return False


def delete_without_where(sqlish: str) -> bool:
      for match in re.finditer(r"\bdelete\s+from\b(?P<body>.*?)(?:;|$)", sqlish, re.IGNORECASE | re.DOTALL):
                body = match.group("body")
                if not re.search(r"\bwhere\b", body, re.IGNORECASE):
                              return True
                      return False


def find_violation(command: str) -> Violation | None:
      for segment in shell_segments(command):
                tokens = parse_tokens(segment)
        if has_rm_force_recursive(tokens):
                      return Violation("rm-rf", "recursive forced removal with rm is blocked")
                  if has_forced_git_push(tokens):
                                return Violation("git-push-force", "forced git push is blocked")

    if looks_like_sql_execution(command):
              if re.search(r"\bdrop\s+table\b", command, re.IGNORECASE):
                            return Violation("drop-table", "DROP TABLE statements are blocked")
                        if re.search(r"\btruncate(?:\s+table)?\b", command, re.IGNORECASE):
                                      return Violation("truncate", "TRUNCATE statements are blocked")
                                  if delete_without_where(command):
                                                return Violation("delete-without-where", "DELETE FROM without WHERE is blocked")

    return None


def project_path(payload: dict) -> str:
      return (
                str(payload.get("cwd") or "")
                or os.environ.get("CLAUDE_PROJECT_DIR")
                or os.getcwd()
      )


def log_block(command: str, payload: dict, violation: Violation) -> None:
      BLOCK_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
              "timestamp": dt.datetime.now(dt.UTC).isoformat(),
              "project_path": project_path(payload),
              "rule": violation.rule,
              "reason": violation.reason,
              "command": command,
    }
    with BLOCK_LOG.open("a", encoding="utf-8") as handle:
              handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_hook() -> int:
      try:
                payload = json.load(sys.stdin)
except json.JSONDecodeError as exc:
        print(f"Invalid hook JSON input: {exc}", file=sys.stderr)
        return 1

    if payload.get("hook_event_name") != "PreToolUse":
              return 0
    if payload.get("tool_name") != "Bash":
              return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
              return 0

    violation = find_violation(command)
    if violation is None:
              return 0

    log_block(command, payload, violation)
    print(
              "Blocked dangerous Bash command before execution: "
              f"{violation.reason}. Review the command and choose a safer, explicit alternative.",
              file=sys.stderr,
    )
    return 2


def install_user_settings() -> int:
      hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    script_path = Path(__file__).resolve()
    try:
              script_path.chmod(script_path.stat().st_mode | stat.S_IXUSR)
except OSError:
        pass

    settings_path = Path.home() / ".claude" / "settings.json"
    if settings_path.exists():
              with settings_path.open("r", encoding="utf-8") as handle:
                            settings = json.load(handle)
else:
        settings = {}

    command = f"python3 {shlex.quote(str(script_path))}"
    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    for matcher in pre_tool_use:
              if matcher.get("matcher") == "Bash":
                            hook_list = matcher.setdefault("hooks", [])
                            if not any(hook.get("command") == command for hook in hook_list):
                                              hook_list.append({"type": "command", "command": command})
                                          break
else:
        pre_tool_use.append(
                      {
                                        "matcher": "Bash",
                                        "hooks": [{"type": "command", "command": command}],
                      }
        )

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    with settings_path.open("w", encoding="utf-8") as handle:
              json.dump(settings, handle, indent=2)
        handle.write("\n")

    print(f"Installed PreToolUse Bash hook in {settings_path}")
    return 0


def main() -> int:
      parser = argparse.ArgumentParser()
    parser.add_argument("--install-user-settings", action="store_true")
    args = parser.parse_args()

    if args.install_user_settings:
              return install_user_settings()
    return run_hook()


if __name__ == "__main__":
      raise SystemExit(main())
