#!/usr/bin/env python3
"""PreToolUse hook that blocks destructive bash commands in Claude Code."""

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")
SHELLS = {"bash", "sh", "zsh", "fish", "dash"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3"}
COMMAND_SEPARATORS = {"&&", "||", ";", "|"}


def shell_words(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.split()


def strip_sql_literals(sql: str) -> str:
    # Avoid treating documentation strings like "DROP TABLE" as executable SQL.
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"'(?:''|[^'])*'", "''", sql)
    sql = re.sub(r'"(?:""|[^"])*"', '""', sql)
    return sql


def has_rm_recursive_force(command: str) -> bool:
    words = shell_words(command)
    for idx, word in enumerate(words):
        if Path(word).name != "rm":
            continue

        recursive = False
        force = False
        for arg in words[idx + 1 :]:
            if arg in COMMAND_SEPARATORS:
                break
            if arg == "--":
                continue
            if not arg.startswith("-"):
                break
            if arg in {"-r", "-R", "--recursive", "--dir"}:
                recursive = True
            if arg in {"-f", "--force"}:
                force = True
            if arg.startswith("-") and not arg.startswith("--"):
                recursive = recursive or "r" in arg.lower()
                force = force or "f" in arg.lower()
        if recursive and force:
            return True
    return bool(re.search(r"\brm\s+-[^\n;|&]*[rR][^\n;|&]*f|\brm\s+-[^\n;|&]*f[^\n;|&]*[rR]", command))


def has_force_push(command: str) -> bool:
    words = shell_words(command)
    for idx, word in enumerate(words):
        if Path(word).name != "git":
            continue

        saw_push = False
        for arg in words[idx + 1 :]:
            if arg in COMMAND_SEPARATORS:
                break
            if not saw_push:
                if arg == "push":
                    saw_push = True
                continue
            if arg in {"-f", "--force", "--force-with-lease"}:
                return True
            if arg.startswith("-") and "f" in arg and not arg.startswith("--"):
                return True
            if arg.startswith("+"):
                return True
    return bool(re.search(r"\bgit\s+push\b[^\n;|&]*(--force(?:-with-lease)?\b|-f\b|\+\S+)", command))


def has_destructive_sql(command: str) -> str | None:
    normalized = strip_sql_literals(command)
    if re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", normalized, re.IGNORECASE):
        return "DROP TABLE/DATABASE/SCHEMA: irreversible database object removal"
    if re.search(r"\bTRUNCATE(\s+TABLE)?\b", normalized, re.IGNORECASE):
        return "TRUNCATE: empties a table without filtering"
    for statement in re.split(r";+", normalized):
        if re.search(r"\bDELETE\s+FROM\b", statement, re.IGNORECASE) and not re.search(
            r"\bWHERE\b", statement, re.IGNORECASE
        ):
            return "DELETE FROM without WHERE: deletes all rows"
    return None


def nested_shell_payloads(command: str) -> list[str]:
    words = shell_words(command)
    payloads: list[str] = []
    for idx, word in enumerate(words[:-1]):
        if Path(word).name not in SHELLS:
            continue
        for offset, arg in enumerate(words[idx + 1 :], start=idx + 1):
            if arg == "-c" and offset + 1 < len(words):
                payloads.append(words[offset + 1])
                break
    return payloads


def sql_client_payloads(command: str) -> list[str]:
    words = shell_words(command)
    payloads: list[str] = []
    for idx, word in enumerate(words[:-1]):
        if Path(word).name not in SQL_CLIENTS:
            continue
        for offset, arg in enumerate(words[idx + 1 :], start=idx + 1):
            if arg in {"-c", "-e", "--execute"} and offset + 1 < len(words):
                payloads.append(words[offset + 1])
                break
    return payloads


def log_block(command: str, project_path: str, reason: str) -> None:
    log_dir = os.path.dirname(LOG_PATH)
    os.makedirs(log_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = {
        "timestamp": ts,
        "project_path": project_path,
        "reason": reason,
        "command": command,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


def check_command(command: str, depth: int = 0) -> str | None:
    if depth > 2:
        return None
    if has_rm_recursive_force(command):
        return "rm -rf: destructive recursive force delete"
    if has_force_push(command):
        return "git push --force/-f/--force-with-lease: rewrites remote history"
    for payload in sql_client_payloads(command):
        reason = has_destructive_sql(payload)
        if reason:
            return reason
    sql_reason = has_destructive_sql(command)
    if sql_reason:
        return sql_reason
    for payload in nested_shell_payloads(command):
        reason = check_command(payload, depth + 1)
        if reason:
            return reason
    return None


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    reason = check_command(command)
    if reason is None:
        sys.exit(0)

    project_path = data.get("cwd", data.get("project_path", ""))
    log_block(command, project_path, reason)

    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked by destructive-command-guard: {reason}. "
                    "If you are sure this is safe, ask the user to bypass the hook."
                ),
            }
        },
        sys.stdout,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
