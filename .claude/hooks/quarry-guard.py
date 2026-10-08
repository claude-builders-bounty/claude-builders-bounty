#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive shell commands."""

import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOK_DIR = Path.home() / ".claude" / "hooks"
LOG_PATH = HOOK_DIR / "blocked.log"

SQL_CLIENTS = {
    "psql", "mysql", "mariadb", "sqlite", "sqlite3", "duckdb", "sqlcmd",
    "isql", "clickhouse-client",
}
WRAPPERS = {"sudo", "doas", "command", "nohup", "env"}
# Wrapper options that consume a following operand; the operand is not the
# wrapped command. Long "--name=value" and attached short values consume
# no next token.
WRAPPER_ARG_OPTS = {
    "sudo": {
        "short": set("ughDCpRrtU"),
        "long": {
            "--user", "--group", "--host", "--chdir", "--close-from",
            "--prompt", "--chroot", "--role", "--type", "--other-user",
        },
    },
    "doas": {"short": set("aCu"), "long": set()},
    "env": {
        "short": set("uCS"),
        "long": {"--unset", "--chdir", "--split-string"},
    },
}
# Wrapper options whose operand is itself a command line; its tokens are
# classified in place instead of being dropped with the option.
WRAPPER_SPLIT_OPTS = {
    "env": {"short": {"S"}, "long": {"--split-string"}},
}
CHAIN_RE = re.compile(r"&&|\|\||;|\n|(?<!\|)\|(?!\|)")
DROP_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
DELETE_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def split_tokens(text):
    try:
        return shlex.split(text, posix=True)
    except ValueError:
        return text.strip().split()


def unwrap(tokens):
    tokens = list(tokens)
    while tokens:
        first = tokens[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", first):
            tokens.pop(0)
            continue
        if first not in WRAPPERS:
            break
        tokens.pop(0)
        if first in {"sudo", "doas", "env"}:
            arg_opts = WRAPPER_ARG_OPTS.get(first, {})
            short_args = arg_opts.get("short", set())
            long_args = arg_opts.get("long", set())
            split_opts = WRAPPER_SPLIT_OPTS.get(first, {})
            split_short = split_opts.get("short", set())
            split_long = split_opts.get("long", set())
            while tokens and tokens[0].startswith("-"):
                opt = tokens.pop(0)
                operand = None
                if opt.startswith("--"):
                    if "=" in opt:
                        name, _, value = opt.partition("=")
                        if name in split_long:
                            operand = value
                    elif opt in long_args and tokens:
                        following = tokens.pop(0)
                        if opt in split_long:
                            operand = following
                else:
                    for idx, char in enumerate(opt[1:], 1):
                        if char in short_args:
                            if idx == len(opt) - 1:
                                if tokens:
                                    following = tokens.pop(0)
                                    if char in split_short:
                                        operand = following
                            elif char in split_short:
                                operand = opt[idx + 1:]
                            break
                if operand is not None:
                    tokens = split_tokens(operand) + tokens
            while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
                tokens.pop(0)
    return tokens


def sql_reason(command, tokens):
    unwrapped = unwrap(tokens)
    if not unwrapped:
        return None
    first = os.path.basename(unwrapped[0]).lower()
    stripped = command.lstrip()
    sql_context = first in SQL_CLIENTS or bool(
        re.match(r"^(DROP\s+TABLE|TRUNCATE\b|DELETE\s+FROM\b)", stripped, re.IGNORECASE)
    )
    if not sql_context:
        return None
    if DROP_RE.search(command):
        return "Blocked DROP TABLE because it irreversibly removes schema and data."
    if TRUNCATE_RE.search(command):
        return "Blocked SQL TRUNCATE because it irreversibly removes all table rows."
    delete = DELETE_RE.search(command)
    if delete and not WHERE_RE.search(command[delete.end():]):
        return "Blocked DELETE FROM without a WHERE clause because it would remove every matching row."
    return None


def rm_reason(tokens):
    tokens = unwrap(tokens)
    if not tokens or os.path.basename(tokens[0]) != "rm":
        return None
    recursive = False
    force = False
    for token in tokens[1:]:
        if token == "--recursive":
            recursive = True
        elif token == "--force":
            force = True
        elif token.startswith("-") and not token.startswith("--"):
            flags = token[1:]
            recursive = recursive or ("r" in flags) or ("R" in flags)
            force = force or ("f" in flags)
    if recursive and force:
        return "Blocked rm with recursive and force flags (rm -rf/-fr/-r -f)."
    return None


def git_reason(tokens):
    tokens = unwrap(tokens)
    if len(tokens) < 2 or os.path.basename(tokens[0]) != "git" or tokens[1] != "push":
        return None
    args = tokens[2:]
    if "--force" in args or "-f" in args:
        return "Blocked git push --force/-f because it rewrites remote history."
    return None


def nested_shell_reason(tokens):
    tokens = unwrap(tokens)
    if len(tokens) < 3:
        return None
    shell = os.path.basename(tokens[0]).lower()
    if shell not in {"sh", "bash", "zsh", "dash"}:
        return None
    if "-c" not in tokens:
        return None
    idx = tokens.index("-c")
    if idx + 1 >= len(tokens):
        return None
    return classify(tokens[idx + 1])


def classify(command):
    if not isinstance(command, str) or not command.strip():
        return None

    full_tokens = split_tokens(command)
    reason = sql_reason(command, full_tokens)
    if reason:
        return reason

    for segment in CHAIN_RE.split(command):
        segment = segment.strip()
        if not segment:
            continue
        tokens = split_tokens(segment)
        for check in (rm_reason, git_reason, nested_shell_reason):
            reason = check(tokens)
            if reason:
                return reason
    return None


def log_block(command, project_path, reason):
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0

    if payload.get("hook_event_name") not in (None, "PreToolUse"):
        return 0
    if payload.get("tool_name") != "Bash":
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str):
        return 0

    reason = classify(command)
    if not reason:
        return 0

    project_path = str(payload.get("cwd") or os.getcwd())
    try:
        log_block(command, project_path, reason)
    except OSError as exc:
        reason = reason + " Logging failed: " + str(exc)

    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                reason + " The blocked attempt was recorded in ~/.claude/hooks/blocked.log."
            ),
        }
    }
    json.dump(response, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
