#!/usr/bin/env python3
"""Guard specified destructive patterns. This is not a shell sandbox."""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys


def sql_reason(text):
    # Strip comments and literals before checking each SQL statement separately.
    clean = re.sub(r"--[^\n]*|/\*.*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"", " ", text, flags=re.S)
    for statement in clean.split(";"):
        if re.search(r"\b(?:DROP\s+TABLE|TRUNCATE)\b", statement, re.I):
            return "DROP TABLE and TRUNCATE are blocked."
        if re.search(r"\bDELETE\s+FROM\b", statement, re.I) and not re.search(r"\bWHERE\b", statement, re.I):
            return "DELETE FROM requires a WHERE clause."
    return None


def reason(command, depth=0):
    if depth > 12:
        return "Nested shell command exceeded the inspection limit."
    # Inspect simple command substitutions even inside otherwise inert echo text.
    for nested in re.findall(r"\$\(([^()]*)\)|`([^`]*)`", command):
        found = reason(next(part for part in nested if part), depth + 1) if any(nested) else None
        if found:
            return found
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";|&()\n")
        lexer.whitespace = " \t\r"
        lexer.whitespace_split = True
        lexer.commenters = "#"
        words = list(lexer)
    except ValueError:
        return "Cannot inspect malformed shell quoting."
    segments = [[]]
    for word in words:
        if word and all(char in ";|&()\n" for char in word):
            segments.append([])
        else:
            segments[-1].append(word)
    for args in segments:
        while args and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", args[0]) or args[0] in {"sudo", "command", "env", "exec", "nohup"}):
            args = args[1:]
        if not args:
            continue
        executable = Path(args[0]).name
        if executable == "rm":
            options = []
            for arg in args[1:]:
                if arg == "--":
                    break
                if arg.startswith("-"):
                    options.append(arg)
            recursive = "--recursive" in options or any("r" in x[1:] or "R" in x[1:] for x in options if not x.startswith("--"))
            force = "--force" in options or any("f" in x[1:] for x in options if not x.startswith("--"))
            if recursive and force:
                return "Recursive forced deletion is blocked."
        if executable == "git":
            subcommand = 1
            while subcommand < len(args) and args[subcommand].startswith("-"):
                subcommand += 2 if args[subcommand] in {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"} else 1
            options = args[subcommand + 1:] if subcommand < len(args) and args[subcommand] == "push" else []
            if any(x in {"-f", "--force", "--force-with-lease", "--force-if-includes"} or x.startswith("--force-with-lease=") or (x.startswith("-") and not x.startswith("--") and "f" in x[1:]) or x.startswith("+") for x in options):
                return "Forced git push is blocked."
        if executable in {"sh", "bash", "zsh", "dash", "ksh"}:
            for index, word in enumerate(args[1:], 1):
                if word.startswith("-") and not word.startswith("--") and "c" in word[1:] and index + 1 < len(args):
                    found = reason(args[index + 1], depth + 1)
                    if found:
                        return found
                    break
        if executable == "eval":
            found = reason(" ".join(args[1:]), depth + 1)
            if found:
                return found
        if executable.lower() in {"drop", "truncate", "delete", "sqlite3", "psql", "mysql", "mariadb", "sqlcmd"}:
            found = sql_reason(" ".join(args))
            if found:
                return found
    return None


def deny(why, command, cwd):
    record = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": command, "project_path": cwd, "reason": why}
    try:
        directory = Path.home() / ".claude" / "hooks"
        directory.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NONBLOCK | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(directory / "blocked.log", flags, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise OSError("Audit log must be a regular file")
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, UnicodeError) as error:
        why += f" Audit logging failed: {error}. The command remains blocked."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": why}}))
    print(why, file=sys.stderr)
    return 2


def main():
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError("Expected an object")
        if data.get("hook_event_name") != "PreToolUse":
            raise ValueError("Expected PreToolUse")
        if data.get("tool_name") != "Bash":
            return 0
        command = data.get("tool_input", {}).get("command")
        if not isinstance(command, str):
            raise ValueError("Expected a command string")
    except (ValueError, AttributeError, TypeError) as error:
        return deny(f"Invalid hook input: {error}", "<invalid input>", "<unknown>")
    why = reason(command)
    return deny(why, command, data.get("cwd", "<unknown>")) if why else 0


if __name__ == "__main__":
    sys.exit(main())
