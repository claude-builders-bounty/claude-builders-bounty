#!/usr/bin/env python3
"""PreToolUse guard for common destructive Bash commands. Never executes input."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shlex
import sys


def sql_reason(statement):
    # Remove comments and quoted values before looking for SQL keywords. A WHERE
    # inside a string, comment or nested SELECT must not exempt the outer DELETE.
    masked = re.sub(r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`", " ", statement)
    for part in masked.split(";"):
        tokens = re.findall(r"[A-Za-z_]+|[()]", part.upper())
        if any(tokens[i:i + 2] == ["DROP", "TABLE"] for i in range(len(tokens))):
            return "DROP TABLE destroys a table; use a reviewed migration."
        if "TRUNCATE" in tokens:
            return "TRUNCATE removes every row; use a reviewed migration."
        for i in range(len(tokens) - 1):
            if tokens[i:i + 2] != ["DELETE", "FROM"]:
                continue
            depth = 0
            has_where = False
            for token in tokens[i + 2:]:
                if token == "(":
                    depth += 1
                elif token == ")":
                    depth -= 1
                    if depth < 0:
                        break
                elif token == "WHERE" and depth == 0:
                    has_where = True
            if not has_where:
                return "DELETE FROM without an outer WHERE clause can delete every row."
    return None


def reason(command, depth=0):
    if depth > 8:
        return "Nested shell command exceeds the inspection limit."
    lexer = shlex.shlex(command.replace("\\\n", ""), posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return "Could not safely parse Bash quoting; split or correct the command."
    segments = [[]]
    for token in tokens:
        if token and all(char in ";&|()\n" for char in token):
            segments.append([])
        else:
            segments[-1].append(token)
    sql_client = any(Path(t).name.lower() in {"psql", "mysql", "mariadb", "sqlite3", "duckdb"} for t in tokens)
    if sql_client:
        for token in tokens:
            found = sql_reason(token)
            if found:
                return found
    for segment in segments:
        while segment:
            if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", segment[0]) or segment[0] in {"then", "do", "!"}:
                segment.pop(0)
                continue
            if segment[0] not in {"sudo", "command", "env"}:
                break
            wrapper = segment.pop(0)
            while segment and segment[0].startswith("-"):
                option = segment.pop(0)
                if option == "--":
                    break
                if ((wrapper == "sudo" and option in {"-u", "-g", "-h", "-p", "-C", "-T", "--user", "--group"})
                        or (wrapper == "env" and option in {"-u", "--unset", "-C", "--chdir"})) and segment:
                    segment.pop(0)
        if not segment:
            continue
        executable = Path(segment[0]).name.lower()
        args = segment[1:]
        if executable in {"bash", "sh", "zsh", "dash"}:
            for i, arg in enumerate(args[:-1]):
                if arg.startswith("-") and "c" in arg[1:]:
                    found = reason(args[i + 1], depth + 1)
                    if found:
                        return found
        if executable == "eval":
            found = reason(" ".join(args), depth + 1)
            if found:
                return found
        if executable == "rm":
            flags = []
            for arg in args:
                if arg == "--":
                    break
                if arg.startswith("-"):
                    flags.append(arg)
            short = "".join(arg[1:] for arg in flags if not arg.startswith("--"))
            if ("r" in short or "R" in short or "--recursive" in flags) and ("f" in short or "--force" in flags):
                return "Recursive forced removal is blocked; inspect the target and use a narrower command."
        if executable == "git" and "push" in args:
            push = args[args.index("push") + 1:]
            if any(a == "-f" or a.startswith("--force") or (a.startswith("-") and not a.startswith("--") and "f" in a[1:]) or a.startswith("+") for a in push):
                return "Forced Git pushes can overwrite shared history; use a normal push."
        if executable.upper() in {"DROP", "DELETE", "TRUNCATE"}:
            found = sql_reason(" ".join(segment))
            if found:
                return found
    return None


def deny(message):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                     "permissionDecision": "deny", "permissionDecisionReason": message}}))


def main():
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise ValueError("Expected an object")
        if payload.get("tool_name") != "Bash":
            return
        command = payload.get("tool_input", {}).get("command")
        if not isinstance(command, str):
            raise ValueError("Missing Bash command")
        blocked = reason(command)
        if not blocked:
            return  # No allow decision: ordinary permission checks still apply.
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), "command": command,
                  "project_path": payload.get("cwd") or os.getcwd(), "reason": blocked}
        try:
            directory = Path.home() / ".claude" / "hooks"
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / "blocked.log"
            if path.is_symlink():
                raise OSError("Log file is a symlink")
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
            descriptor = os.open(path, flags, 0o600)
            with os.fdopen(descriptor, "a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, ensure_ascii=True) + "\n")
        except OSError as error:
            blocked += f" Audit log could not be written: {error}. The command remains blocked."
        deny(blocked)
    except (ValueError, TypeError, AttributeError) as error:
        deny(f"Invalid hook input: {error}. Command was not approved.")


if __name__ == "__main__":
    main()
