#!/usr/bin/env python3
"""Inspect PreToolUse Bash inputs; never execute, expand, or read their commands.

This is a guard for explicit commands, not a shell interpreter or a sandbox.
Aliases, variable expansion, sourced files and dynamically constructed commands
require the caller's normal permission controls.
"""

import argparse
import json
import os
from pathlib import Path
import re
import sys
from datetime import datetime, timezone


ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
SQL_TOKEN = re.compile(
    r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|\\.|[^'])*'|"
    r'"(?:""|\\.|[^"])*"|`(?:``|[^`])*`|\[[^\]]*\]|'
    r"[A-Za-z_][A-Za-z0-9_$]*|;"
)
HEREDOC_HEADER = re.compile(
    r"<<(?P<tabs>-?)[ \t]*(?:'([^'\n]+)'|\"([^\"\\\n]+)\"|([A-Za-z_][A-Za-z0-9_]*))"
    r"(?=[ \t\r\n;&|)]|$)"
)


def shell_segments(command):
    """Split literal words and command separators, preserving quoted separators."""
    segments, words, word = [], [], []
    quote, started, begin, i = None, False, 0, 0

    def flush_word():
        nonlocal started
        if started:
            words.append("".join(word))
            word.clear()
            started = False

    def flush_segment(end):
        flush_word()
        if words:
            segments.append((words[:], command[begin:end]))
            words.clear()

    while i < len(command):
        char = command[i]
        if quote:
            if char == quote:
                quote = None
            elif char == "\\" and quote == '"' and i + 1 < len(command) and command[i + 1] in '\\"$`\n':
                i += 1
                if command[i] != "\n":
                    word.append(command[i])
            else:
                word.append(char)
        elif char in "'\"":
            quote, started = char, True
        elif char == "\\":
            if i + 1 == len(command):
                raise ValueError("unfinished shell escape")
            i += 1
            if command[i] != "\n":
                word.append(command[i])
                started = True
        elif char == "#" and not started:
            flush_segment(i)
            while i < len(command) and command[i] != "\n":
                i += 1
            begin = i
            continue
        elif char in ";|&()\n":
            flush_segment(i)
            begin = i + 1
        elif char.isspace():
            flush_word()
        else:
            word.append(char)
            started = True
        i += 1
    if quote:
        raise ValueError("unterminated shell quote")
    flush_segment(len(command))
    return segments


def executable_words(words):
    """Recognize assignments and simple env/sudo/command/exec wrappers."""
    words = words[:]
    value_options = {"-u", "-g", "-p", "-h", "-C", "-T", "--user", "--group", "--chdir"}
    while words:
        if ASSIGNMENT.match(words[0]):
            words.pop(0)
            continue
        name = words[0].rsplit("/", 1)[-1]
        if name not in {"env", "sudo", "command", "exec"}:
            return name, words[1:]
        words.pop(0)
        while words and words[0].startswith("-"):
            option = words.pop(0)
            if option == "--":
                break
            if option in {"--help", "--version"} or (name == "command" and option in {"-v", "-V"}):
                return "", []
            if name == "sudo" and option in {"-l", "--list", "-v", "--validate", "-V"}:
                return "", []
            if (name == "sudo" and option in value_options) or (name == "env" and option in {"-u", "--unset", "-C", "--chdir"}) or (name == "exec" and option == "-a"):
                if words:
                    words.pop(0)
            elif name == "env" and option in {"-S", "--split-string"}:
                return "", []  # Dynamic wrapper syntax is outside this lexer.
    return "", []


def literal_heredoc_data(command):
    """Hide only complete, quoted heredoc data for standalone cat/tee commands.

    Pipelines, other consumers, multiple heredocs and unquoted delimiters are
    deliberately not treated as inert data. Return text solely for inspection;
    the caller retains the original command for its audit record.
    """
    output, pending = [], []
    quote, line_begin, copied, i = None, 0, 0, 0
    while i < len(command):
        char = command[i]
        if quote:
            if char == quote:
                quote = None
            elif char == "\\" and quote == '"' and i + 1 < len(command):
                i += 1
        elif char == "\\":
            i += 1
        elif char in "'\"":
            quote = char
        elif char == "#" and (i == 0 or command[i - 1].isspace()):
            while i < len(command) and command[i] != "\n":
                i += 1
            continue
        elif command.startswith("<<", i):
            match = HEREDOC_HEADER.match(command, i)
            pending.append(match)
            i = match.end() - 1 if match else i + 1
        elif char == "\n":
            if pending:
                if len(pending) != 1 or pending[0] is None:
                    return command  # Do not mistake unknown heredoc data for headers.
                match = pending[0]
                delimiter = match.group(2) or match.group(3) or match.group(4)
                tabs = r"\t*" if match.group("tabs") else ""
                end = re.compile(r"^" + tabs + re.escape(delimiter) + r"(?:\n|$)", re.MULTILINE).search(command, i + 1)
                if not end:
                    return command
                header = shell_segments(command[line_begin:i])
                if not match.group(4) and len(header) == 1 and executable_words(header[0][0])[0] in {"cat", "tee"}:
                    output.append(command[copied:i + 1])
                    output.append("\n" * command[i + 1:end.end()].count("\n"))
                    copied = end.end()
                # Leave evaluated/other-consumer bodies intact for inspection,
                # without recursively treating their text as heredoc headers.
                i = line_begin = end.end()
                pending.clear()
                continue
            pending.clear()
            line_begin = i + 1
        i += 1
    output.append(command[copied:])
    return "".join(output)


def sql_reason(query):
    """Inspect SQL keywords outside comments/literals, separately per statement."""
    statement = []
    for match in SQL_TOKEN.finditer(query + ";"):
        token = match.group()
        if token == ";":
            if statement and statement[0] == "TRUNCATE":
                return "SQL TRUNCATE is blocked."
            for i in range(len(statement) - 1):
                pair = statement[i:i + 2]
                if pair == ["DROP", "TABLE"]:
                    return "SQL DROP TABLE is blocked."
                if pair == ["DELETE", "FROM"] and "WHERE" not in statement[i + 2:]:
                    return "SQL DELETE FROM without a WHERE clause in that statement is blocked."
            statement = []
        elif token[0].isalpha() or token[0] == "_":
            statement.append(token.upper())
    return None


def sql_arguments(program, args):
    flags = {
        "psql": {"-c", "--command"}, "mysql": {"-e", "--execute"},
        "mariadb": {"-e", "--execute"}, "sqlcmd": {"-Q", "-q"},
        "duckdb": {"-c", "--command", "-s"}, "sqlite3": {"-cmd"},
    }
    queries, positional, i = [], [], 0
    while i < len(args):
        arg = args[i]
        if arg in flags[program] and i + 1 < len(args):
            i += 1
            queries.append(args[i])
        elif any(arg.startswith(flag + "=") for flag in flags[program] if flag.startswith("--")):
            queries.append(arg.split("=", 1)[1])
        elif program in {"mysql", "mariadb", "psql"} and len(arg) > 2 and arg[:2] in flags[program]:
            queries.append(arg[2:])
        elif program == "sqlite3" and arg in {"-init", "-separator", "-newline", "-nullvalue"}:
            i += 1
        elif program in {"sqlite3", "duckdb"} and not arg.startswith("-"):
            positional.append(arg)
        i += 1
    if program in {"sqlite3", "duckdb"} and len(positional) > 1:
        queries.extend(positional[1:])  # First positional argument is the database.
    return queries


def command_reason(command):
    command = literal_heredoc_data(command)
    if re.match(r"^\s*(DROP|TRUNCATE|DELETE)\b", command, re.IGNORECASE):
        return sql_reason(command)  # SQL text may contain unquoted newlines.
    for words, source in shell_segments(command):
        program, args = executable_words(words)
        if program == "rm":
            recursive = force = False
            for arg in args:
                if arg == "--":
                    break
                recursive |= arg == "--recursive" or (arg.startswith("-") and not arg.startswith("--") and any(c in arg[1:] for c in "rR"))
                force |= arg == "--force" or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:])
            if recursive and force:
                return "Recursive force removal (rm with recursive and force flags) is blocked."
        elif program == "git":
            i = 0
            while i < len(args) and args[i].startswith("-"):
                option = args[i]
                i += 2 if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"} else 1
            if i < len(args) and args[i] == "push":
                for arg in args[i + 1:]:
                    if arg == "--":
                        break
                    if arg == "--force" or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]):
                        return "Git force push is blocked."
        elif program in {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "duckdb"}:
            for query in sql_arguments(program, args):
                reason = sql_reason(query)
                if reason:
                    return reason
        elif program.upper() in {"DROP", "TRUNCATE", "DELETE"}:
            reason = sql_reason(source)
            if reason:
                return reason
    return None


def deny(reason, command, cwd, hooks_dir):
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(),
             "command": command, "cwd": cwd, "reason": reason}
    try:
        hooks_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(hooks_dir / "blocked.log", flags, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as log:
            log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except (OSError, UnicodeError) as error:
        reason += f" Audit log could not be written ({type(error).__name__}); command remains blocked."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hooks-dir", type=Path, help="Explicit directory for isolated logs")
    args = parser.parse_args()
    hooks_dir = args.hooks_dir if args.hooks_dir is not None else Path.home() / ".claude" / "hooks"
    try:
        event = json.load(sys.stdin)
    except (ValueError, UnicodeError):
        deny("Guard received invalid JSON; inspection is unavailable.", "<unavailable>", None, hooks_dir)
        return
    if not isinstance(event, dict):
        deny("Guard requires a JSON object event.", "<unavailable>", None, hooks_dir)
        return
    if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
        return
    tool_input, cwd = event.get("tool_input"), event.get("cwd")
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    if not isinstance(command, str) or not isinstance(cwd, str):
        deny("Bash event requires string command and cwd fields.",
             command if isinstance(command, str) else "<unavailable>",
             cwd if isinstance(cwd, str) else None, hooks_dir)
        return
    try:
        reason = command_reason(command)
    except ValueError as error:
        reason = f"Guard could not parse the command: {error}."
    if reason:
        deny(reason, command, cwd, hooks_dir)


if __name__ == "__main__":
    main()
