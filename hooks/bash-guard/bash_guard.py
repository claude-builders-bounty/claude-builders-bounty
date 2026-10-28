#!/usr/bin/env python3
"""A bounded, non-executing command policy for Claude Code's Bash tool."""

import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone


MAX_INPUT = 1024 * 1024
MAX_DEPTH = 16
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "duckdb"}
SHELLS = {"sh", "bash", "dash", "zsh", "ksh"}
# Wrapper options that consume the next word; env/others default to -u/-C style.
OPTIONS_WITH_VALUE = {
    "sudo": {"-u", "-g", "-h", "-p", "-C", "-R", "-D"},
    "doas": {"-u", "-C"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "stdbuf": {"-i", "-o", "-e", "--input", "--output", "--error"},
}
FIND_EXEC = {"-exec", "-execdir", "-ok", "-okdir"}
XARGS_OPTIONS_WITH_VALUE = {"-I", "-n", "-L", "-P", "-s", "-d", "-E", "-a", "--arg-file", "--delimiter",
                            "--max-args", "--max-lines", "--max-procs", "--max-chars", "--eof", "--replace"}


@dataclass
class Token:
    text: str
    start: int
    end: int
    kind: str = "word"


def lex_shell(source, depth=0):
    """Read words, operators, literal here-docs and executable substitutions.

    No variables, aliases, globs, files or external commands are evaluated.
    Quotes are removed only from shell words, not from their SQL contents.
    """
    if depth > MAX_DEPTH:
        raise ValueError("command nesting exceeds the inspection limit")
    tokens, substitutions, pending = [], [], []
    i, length = 0, len(source)
    while i < length:
        if source[i] in " \t\r":
            i += 1
            continue
        if source[i] == "#":
            end = source.find("\n", i)
            i = length if end < 0 else end
            continue
        if source[i] == "\n":
            i += 1
            for delimiter, strip_tabs, expand in pending:
                lines = []
                start = i
                while i < length:
                    end = source.find("\n", i)
                    end = length if end < 0 else end
                    line = source[i:end]
                    i = min(end + 1, length)
                    if (line.lstrip("\t") if strip_tabs else line) == delimiter:
                        break
                    lines.append(line.lstrip("\t") if strip_tabs else line)
                else:
                    raise ValueError("unterminated here-document")
                body = "\n".join(lines)
                tokens.append(Token(body, start, i, "input"))
                if expand:
                    # Only substitutions execute in a here-doc, not its plain text.
                    position = 0
                    while position < len(body):
                        if body[position] == "\\":
                            position += 2
                        elif body.startswith("$(", position) or body[position] == "`":
                            nested, position = substitution(body, position)
                            substitutions.append(nested)
                        else:
                            position += 1
            pending.clear()
            tokens.append(Token(";", i, i, "op"))
            continue
        if source[i] in ";|&()<>":
            match = re.match(r"<<<|<<-|<<|>>|&&|\|\||[;|&()<>]", source[i:])
            op = match.group()
            tokens.append(Token(op, i, i + len(op), "op"))
            i += len(op)
            continue
        start, chars, quote = i, [], None
        while i < length:
            c = source[i]
            if quote is None and (c.isspace() or c in ";|&()<>"):
                break
            if c == "\\" and quote != "'":
                if i + 1 >= length:
                    raise ValueError("unfinished shell escape")
                following = source[i + 1]
                if quote == '"' and following not in '$`"\\\n':
                    chars.append(c)
                    i += 1
                    continue
                if following != "\n":
                    chars.append(following)
                i += 2
                continue
            if c in "'\"" and (quote is None or quote == c):
                quote = c if quote is None else None
                i += 1
                continue
            if quote != "'" and (source.startswith("$(", i) or c == "`"):
                body, i = substitution(source, i)
                substitutions.append(body)
                chars.append("$SUBSTITUTION")
                continue
            chars.append(c)
            i += 1
        if quote:
            raise ValueError("unterminated shell quote")
        if not chars and source[start:i].replace("\\\n", "") == "":
            continue
        word = Token("".join(chars), start, i)
        tokens.append(word)
        if len(tokens) > 1 and tokens[-2].text in {"<<", "<<-"} and tokens[-2].kind == "op":
            raw = source[start:i]
            pending.append((word.text, tokens[-2].text == "<<-", not any(c in raw for c in "'\"\\")))
    if pending:
        raise ValueError("missing here-document body")
    return tokens, substitutions


def substitution(source, start):
    """Return a literal substitution body, respecting its nested quotes."""
    backtick = source[start] == "`"
    i = start + (1 if backtick else 2)
    body_start, level, quote = i, 1, None
    while i < len(source):
        c = source[i]
        if c == "\\" and quote != "'":
            i += 2
            continue
        if backtick and c == "`":
            return source[body_start:i], i + 1
        if c in "'\"" and (quote is None or quote == c):
            quote = c if quote is None else None
        elif not backtick and quote is None:
            if c == "(":
                level += 1
            elif c == ")":
                level -= 1
                if not level:
                    return source[body_start:i], i + 1
        i += 1
    raise ValueError("unterminated command substitution")


def sql_tokens(source):
    """Tokenize SQL without treating strings, identifiers or comments as keywords."""
    result, i, depth = [], 0, 0
    while i < len(source):
        c = source[i]
        if c.isspace():
            i += 1
            continue
        if source.startswith("--", i) or c == "#":
            end = source.find("\n", i)
            i = len(source) if end < 0 else end
            continue
        if source.startswith("/*", i):
            if source.startswith("/*!", i):
                raise ValueError("executable SQL comments need manual review")
            level, i = 1, i + 2
            while i < len(source) and level:
                if source.startswith("/*", i):
                    level, i = level + 1, i + 2
                elif source.startswith("*/", i):
                    level, i = level - 1, i + 2
                else:
                    i += 1
            if level:
                raise ValueError("unterminated SQL comment")
            continue
        dollar = re.match(r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$", source[i:])
        if dollar:
            mark = dollar.group()
            end = source.find(mark, i + len(mark))
            if end < 0:
                raise ValueError("unterminated SQL dollar string")
            result.append(("<quoted>", depth))
            i = end + len(mark)
            continue
        if c in "'\"`[":
            close = "]" if c == "[" else c
            i += 1
            while i < len(source):
                if source[i] == close:
                    if i + 1 < len(source) and source[i + 1] == close:
                        i += 2
                        continue
                    i += 1
                    break
                if source[i] == "\\" and c == "'":
                    i += 2
                else:
                    i += 1
            else:
                raise ValueError("unterminated SQL quote")
            result.append(("<quoted>", depth))
            continue
        word = re.match(r"[A-Za-z_][A-Za-z_0-9$]*", source[i:])
        if word:
            result.append((word.group().upper(), depth))
            i += len(word.group())
        else:
            if c == ")":
                depth -= 1
            result.append((c, depth))
            if c == "(":
                depth += 1
            i += 1
    return result


def sql_reason(source):
    tokens = sql_tokens(source)
    for i, (word, level) in enumerate(tokens):
        following = tokens[i + 1] if i + 1 < len(tokens) else None
        if word == "DROP" and following == ("TABLE", level):
            return "DROP TABLE removes a table."
        if word == "TRUNCATE" and (i == 0 or tokens[i - 1][0] == ";"):
            return "TRUNCATE removes all rows."
        if word == "DELETE" and following == ("FROM", level):
            has_where = False
            for next_word, next_level in tokens[i + 2:]:
                if next_level < level or next_word == ";":
                    break
                if next_level == level and next_word in {"RETURNING", "ORDER", "LIMIT"}:
                    break
                if next_word == "WHERE" and next_level == level:
                    has_where = True
                    break
            if not has_where:
                return "DELETE FROM has no WHERE clause in the same statement."
    return None


def executable_words(tokens):
    """Discard redirections, assignments and common literal command wrappers."""
    words, inputs, skip = [], [], False
    for index, token in enumerate(tokens):
        if token.kind == "input":
            inputs.append(token.text)
        elif skip:
            skip = False
        elif token.kind == "op" and token.text in {"<", ">", ">>", "<<", "<<-", "<<<"}:
            if token.text == "<<<":
                # Its following word is data passed to this executable.
                inputs.append(tokens[index + 1].text if index + 1 < len(tokens) else "")
            skip = True
        elif token.kind == "word":
            if (token.text.isdigit() and index + 1 < len(tokens)
                    and tokens[index + 1].kind == "op" and tokens[index + 1].text in {"<", ">", ">>"}
                    and token.end == tokens[index + 1].start):
                continue
            words.append(token.text)
    while words:
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", words[0]) or words[0] in {"!", "if", "then", "do", "elif"}:
            words.pop(0)
        elif words[0] in {"sudo", "doas", "env", "command", "exec", "nohup", "time", "nice", "timeout", "stdbuf"}:
            wrapper = words.pop(0)
            while words and words[0].startswith("-"):
                option = words.pop(0)
                if option == "--":
                    break
                if wrapper == "env" and (option in {"-S", "--split-string"} or option.startswith("--split-string=") or option.startswith("-S")):
                    if option in {"-S", "--split-string"}:
                        if not words:
                            raise ValueError("env split-string is missing its literal argument")
                        value = words.pop(0)
                    else:
                        value = option.split("=", 1)[1] if option.startswith("--") else option[2:]
                    # env splits literal words; it does not run shell operators
                    # or substitutions inside this already-quoted argument.
                    words[:0] = shlex.split(value, comments=False, posix=True)
                    continue
                if option in OPTIONS_WITH_VALUE.get(wrapper, {"-u", "--unset", "-C", "--chdir"}):
                    if words:
                        words.pop(0)
            if wrapper == "timeout" and words:
                words.pop(0)  # the duration
        else:
            break
    return words, inputs


def command_reason(command, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError("command nesting exceeds the inspection limit")
    # Also recognize the issue's bare SQL examples, including newlines between
    # keywords. SQL passed to an actual client is handled below as one argument.
    direct = re.match(r"^\s*(DROP|DELETE|TRUNCATE)\b", command, re.I)
    if direct and not (direct.group(1) == "truncate" and re.search(r"(?:^|\s)-\S", command)):
        reason = sql_reason(command)
        if reason:
            return reason
    tokens, substitutions = lex_shell(command, depth)
    for body in substitutions:
        reason = command_reason(body, depth + 1)
        if reason:
            return reason
    segments, current = [], []
    for token in tokens:
        if token.kind == "op" and token.text in {";", "&&", "||", "|", "&", "(", ")"}:
            if current:
                segments.append((current, token.text))
                current = []
        else:
            current.append(token)
    if current:
        segments.append((current, None))
    for index, (segment, _) in enumerate(segments):
        words, inputs = executable_words(segment)
        if not words:
            continue
        name, args = words[0].rsplit("/", 1)[-1], words[1:]
        launched = []
        if name == "find":
            j = 0
            while j < len(args):
                if args[j] in FIND_EXEC:
                    end = j + 1
                    while end < len(args) and args[end] not in {";", "+"}:
                        end += 1
                    launched.append(args[j + 1:end])
                    j = end
                j += 1
        elif name == "xargs":
            j = 0
            while j < len(args) and args[j].startswith("-"):
                option = args[j]
                j += 1
                if option == "--":
                    break
                if option in XARGS_OPTIONS_WITH_VALUE:
                    j += 1
            launched.append(args[j:])
        for sub in launched:
            if sub:
                reason = command_reason(shlex.join(sub), depth + 1)
                if reason:
                    return reason
        if name == "rm":
            recursive, force = False, False
            for arg in args:
                if arg == "--":
                    break
                recursive |= arg == "--recursive" or (arg.startswith("-") and not arg.startswith("--") and any(c in arg[1:] for c in "rR"))
                force |= arg == "--force" or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:])
            if recursive and force:
                return "rm combines recursive and force options."
        if name == "git":
            j = 0
            while j < len(args) and args[j].startswith("-"):
                option = args[j]
                j += 2 if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"} else 1
            if j < len(args) and args[j] == "push":
                for arg in args[j + 1:]:
                    if arg in {"-f", "--force", "--force-with-lease"} or arg.startswith("--force-with-lease=") or arg.startswith("+") or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]):
                        return "git push requests a forced update."
        if name in SHELLS or name == "eval":
            scripts = list(inputs)
            if name == "eval":
                scripts.append(" ".join(args))
            else:
                for j, arg in enumerate(args[:-1]):
                    if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                        scripts.append(args[j + 1])
                        break
            for script in scripts:
                reason = command_reason(script, depth + 1)
                if reason:
                    return reason
        sql = []
        if name in SQL_CLIENTS:
            sql.extend(inputs)
            # Literal SQL passed via -c/-e/-Q, positional arguments, or a pipe.
            for arg in args:
                if arg.startswith(("--command=", "--execute=", "--query=")):
                    arg = arg.split("=", 1)[1]
                elif arg.startswith(("-c", "-e", "-Q")) and len(arg) > 2:
                    arg = arg[2:]
                if re.search(r"\b(?:DROP|TRUNCATE|DELETE)\b", arg, re.I):
                    sql.append(arg)
            if index and segments[index - 1][1] == "|":
                previous, _ = executable_words(segments[index - 1][0])
                if previous and previous[0] in {"echo", "printf"}:
                    sql.append(" ".join(previous[1:]))
        elif name.upper() in {"DROP", "DELETE", "TRUNCATE"}:
            # Do not confuse the Unix `truncate -s SIZE FILE` utility with SQL.
            if name != "truncate" or not any(arg.startswith("-") for arg in args):
                sql.append(command[segment[0].start:segment[-1].end])
        for statement in sql:
            reason = sql_reason(statement)
            if reason:
                return reason
    return None


def append_log(command, project_path, reason):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "command": command,
              "project_path": project_path, "reason": reason}
    data = (json.dumps(record, ensure_ascii=False) + "\n").encode("utf-8")
    path = Path(__file__).resolve().parent / "blocked.log"
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    fd = os.open(path, flags, 0o600)
    locked = False
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError("blocked.log is not a regular file")
        # Windows O_APPEND alone does not serialize the seek-and-write. Lock
        # byte zero (including on an empty file) before appending a full record.
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        locked = True
        if os.name == "posix":
            os.fchmod(fd, 0o600)
        os.lseek(fd, 0, os.SEEK_END)
        if os.write(fd, data) != len(data):
            raise OSError("incomplete log write")
    finally:
        try:
            if locked and os.name == "nt":
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        finally:
            os.close(fd)  # Also releases the POSIX lock.


def deny(command, project_path, reason):
    reason = "Blocked: " + reason
    try:
        append_log(command, project_path, reason)
    except (OSError, UnicodeError) as exc:
        reason += f" Audit log could not be written ({type(exc).__name__}); the command is still denied."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "deny", "permissionDecisionReason": reason}}))


def main():
    command, project_path = None, None
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        if len(raw) > MAX_INPUT:
            raise ValueError("hook input exceeds 1 MiB")
        event = json.loads(raw.decode("utf-8"))
        if not isinstance(event, dict):
            raise ValueError("expected a JSON object")
        if event.get("hook_event_name") != "PreToolUse" or event.get("tool_name") != "Bash":
            if isinstance(event.get("hook_event_name"), str) and isinstance(event.get("tool_name"), str):
                return 0
            raise ValueError("missing hook event or tool name")
        tool_input = event.get("tool_input")
        command = tool_input.get("command") if isinstance(tool_input, dict) else None
        project_path = event.get("cwd")
        if not isinstance(command, str) or not isinstance(project_path, str) or not project_path:
            raise ValueError("Bash input needs a string command and nonempty cwd")
        if "\x00" in command or "\x00" in project_path:
            raise ValueError("NUL characters are not valid command input")
        reason = command_reason(command)
        if reason:
            deny(command, project_path, reason)
    except (ValueError, UnicodeError, RecursionError) as exc:
        deny(command, project_path, f"Cannot inspect this Bash request: {exc}.")
    except Exception as exc:
        # Exit 2 is a blocking hook error even if JSON cannot be produced.
        print(f"Blocked: command inspection failed ({type(exc).__name__}).", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
