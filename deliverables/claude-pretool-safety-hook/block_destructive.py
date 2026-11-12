#!/usr/bin/env python3
"""Claude Code PreToolUse hook: deny high-risk destructive Bash commands."""
from __future__ import annotations
import json, os, re, shlex, sys
from datetime import datetime, timezone
from pathlib import Path

SQL_DELETE = re.compile(r"\bDELETE\s+FROM\b(?P<body>[^;]*)", re.IGNORECASE)
SQL_DROP = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
SQL_TRUNCATE = re.compile(r"\bTRUNCATE(?:\s+TABLE)?\b", re.IGNORECASE)

def _segments(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    current = []
    for token in lexer:
        if token and all(ch in ";&|" for ch in token):
            if current:
                yield " ".join(current)
                current = []
        else:
            current.append(token)
    if current:
        yield " ".join(current)

def _command_tokens(segment):
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        return [segment]
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", token):
            i += 1
        elif token in {"sudo", "command", "builtin", "nohup"}:
            i += 1
        elif token == "env":
            i += 1
            while i < len(tokens) and (tokens[i].startswith("-") or "=" in tokens[i]):
                i += 1
        else:
            break
    return tokens[i:]

def inspect_command(command):
    for segment in _segments(command):
        tokens = _command_tokens(segment)
        if not tokens:
            continue
        executable = Path(tokens[0]).name
        if executable in {"psql", "sqlite3", "mysql", "mariadb", "duckdb", "sqlcmd"}:
            if SQL_DROP.search(segment):
                return True, "DROP TABLE destroys a table and is blocked by the safety hook."
            if SQL_TRUNCATE.search(segment):
                return True, "TRUNCATE removes table data and is blocked by the safety hook."
            for match in SQL_DELETE.finditer(segment):
                if not re.search(r"\bWHERE\b", match.group("body"), re.IGNORECASE):
                    return True, "Unconditional DELETE FROM can remove every row; add a WHERE clause."
        if executable == "rm":
            recursive = force = False
            for token in tokens[1:]:
                if token == "--":
                    break
                if token.startswith("--"):
                    option = token.split("=", 1)[0]
                    recursive |= option == "--recursive"
                    force |= option == "--force"
                elif token.startswith("-") and not token.startswith("--"):
                    recursive |= "r" in token[1:] or "R" in token[1:]
                    force |= "f" in token[1:]
            if recursive and force:
                return True, "rm with both recursive and force flags can irreversibly delete directory trees."
        if executable == "git":
            try:
                push_at = tokens.index("push", 1)
            except ValueError:
                push_at = -1
            if push_at >= 0 and any(arg in {"-f", "--force", "--force-with-lease", "--force-if-includes"} for arg in tokens[push_at + 1:]):
                return True, "Force-pushing can overwrite remote history and is blocked by the safety hook."
    return False, ""

def _log_block(command, project_path, reason):
    log_path = Path.home() / ".claude" / "hooks" / "blocked.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {"timestamp": datetime.now(timezone.utc).isoformat(),
              "command": command.replace("\r", " ").replace("\n", " ")[:4000],
              "project_path": project_path, "reason": reason}
    with log_path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")

def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        print(json.dumps({"continue": True}))
        return 0
    if payload.get("tool_name") != "Bash":
        print("{}")
        return 0
    tool_input = payload.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    blocked, reason = inspect_command(command)
    if not blocked:
        print("{}")
        return 0
    _log_block(command, str(payload.get("cwd") or os.getcwd()), reason)
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason
    }}))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
