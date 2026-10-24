#!/usr/bin/env python3
"""Bounded, standard-library-only Claude Code PreToolUse guard.

This is a guardrail for literal commands, not a shell interpreter or sandbox.
It never evaluates the supplied command.
"""
import datetime
import json
import os
from pathlib import Path
import re
import shlex
import sys

MAX_INPUT = 1_048_576
CLIENTS = {"sqlite3", "psql", "mysql", "mariadb", "duckdb", "sqlcmd"}
SEPARATORS = {";", "&&", "||", "|", "&", "(", ")"}


def sql_tokens(text):
    """Discard SQL string/comment contents, retain statement/depth boundaries."""
    pattern = r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\"(?:\"\"|[^\"])*\"|`[^`]*`|\[[^\]]*\]|[A-Za-z_][A-Za-z_0-9]*|[;()]"
    for match in re.finditer(pattern, text):
        token = match.group()
        if token.startswith(("--", "/*")):
            continue
        if token[0] in "'\"`[":
            yield "<quoted>"
        else:
            yield token.upper()


def sql_reason(text):
    statements, current = [], []
    for token in sql_tokens(text):
        if token == ";":
            statements.append(current)
            current = []
        else:
            current.append(token)
    statements.append(current)
    for tokens in statements:
        depth = 0
        top = []
        for token in tokens:
            if token == "(":
                depth += 1
            elif token == ")":
                depth = max(0, depth - 1)
            elif depth == 0:
                top.append(token)
        # Also examine nested SQL for DROP/TRUNCATE and DELETE statements.
        if any(tokens[i:i + 2] == ["DROP", "TABLE"] for i in range(len(tokens))):
            return "DROP TABLE removes a table and its data."
        if "TRUNCATE" in tokens:
            return "TRUNCATE removes all rows."
        for index in range(len(top) - 1):
            if top[index:index + 2] == ["DELETE", "FROM"] and "WHERE" not in top[index + 2:]:
                return "DELETE FROM has no top-level WHERE clause in its statement."
    return None


def executable(words):
    """Unwrap common literal command prefixes without executing anything."""
    words = list(words)
    while words:
        name = Path(words[0]).name
        if re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*=.*", words[0]):
            words.pop(0)
        elif name in {"command", "builtin", "exec", "nohup"}:
            words.pop(0)
            while words and words[0] in {"--", "-p"}:
                words.pop(0)
        elif name == "sudo":
            words.pop(0)
            while words and words[0].startswith("-"):
                option = words.pop(0)
                if option in {"-u", "-g", "-h", "-p", "-C", "-T"} and words:
                    words.pop(0)
                if option == "--":
                    break
        elif name == "env":
            words.pop(0)
            while words and (words[0].startswith("-") or "=" in words[0]):
                option = words.pop(0)
                if option in {"-u", "--unset", "-C", "--chdir"} and words:
                    words.pop(0)
        else:
            break
    return words


def segment_reason(words, nesting):
    words = executable(words)
    if not words:
        return None
    name, args = Path(words[0]).name, words[1:]
    if name == "rm":
        recursive = force = False
        for arg in args:
            if arg == "--":
                break
            if arg in {"--recursive"}:
                recursive = True
            elif arg in {"--force"}:
                force = True
            elif arg.startswith("-") and not arg.startswith("--"):
                recursive |= "r" in arg[1:] or "R" in arg[1:]
                force |= "f" in arg[1:]
        if recursive and force:
            return "Recursive forced removal (rm with recursive and force flags) is blocked."
    if name == "git":
        index = 0
        while index < len(args) and args[index].startswith("-"):
            option = args[index]
            index += 1
            if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
                index += 1
        if index < len(args) and args[index] == "push":
            for arg in args[index + 1:]:
                if arg == "--":
                    break
                if arg == "--force" or arg.startswith("--force-with-lease") or arg.startswith("--force=") or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]) or arg.startswith("+"):
                    return "Forced git push can overwrite remote history."
    if name in {"bash", "sh", "zsh", "dash", "ksh"}:
        for index, arg in enumerate(args):
            if arg.startswith("-") and "c" in arg[1:] and index + 1 < len(args):
                return command_reason(args[index + 1], nesting + 1)
    if name in CLIENTS:
        return sql_reason(" ".join(args))
    # Recognize direct SQL input too, even though Bash alone cannot run it.
    if name.upper() in {"DROP", "TRUNCATE", "DELETE"}:
        return sql_reason(" ".join(words))
    return None


def command_reason(command, nesting=0):
    if nesting > 8:
        return "Nested shell command exceeds the inspection limit."
    try:
        lexer = shlex.shlex(command.replace("\\\n", ""), posix=True, punctuation_chars=";&|()\n")
        lexer.whitespace = " \t\r"
        lexer.commenters = "#"
        words = list(lexer)
    except ValueError:
        return "Command could not be parsed safely (unclosed shell quoting)."
    segment = []
    for word in words + [";"]:
        if word in SEPARATORS or word == "\n" or (word and all(c in ";&|()\n" for c in word)):
            reason = segment_reason(segment, nesting)
            if reason:
                return reason
            segment = []
        else:
            segment.append(word)
    return None


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "Destructive-command guard: " + reason}}))


def main():
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError("hook input exceeds 1 MiB")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("hook input must be an object")
        if event.get("tool_name") != "Bash":
            return
        tool_input = event.get("tool_input")
        if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
            raise ValueError("Bash command must be a string")
        command = tool_input["command"]
        reason = command_reason(command)
        if reason:
            record = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": command, "project_path": event.get("cwd", ""), "reason": reason}
            try:
                folder = Path.home() / ".claude" / "hooks"
                folder.mkdir(parents=True, exist_ok=True, mode=0o700)
                flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
                fd = os.open(folder / "blocked.log", flags, 0o600)
                with os.fdopen(fd, "a", encoding="utf-8") as log:
                    log.write(json.dumps(record, ensure_ascii=True) + "\n")
            except OSError:
                reason += " Audit log could not be written; the command remains denied."
            deny(reason)
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        deny("Invalid hook input: " + str(error))


if __name__ == "__main__":
    main()
