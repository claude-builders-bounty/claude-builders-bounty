#!/usr/bin/env python3
"""Offline PreToolUse guard for literal destructive Bash commands.

This is a static accident-prevention guard, not a Bash interpreter or sandbox.
It never executes the command being inspected. See README.md for limitations.
"""

import datetime
import json
import os
from pathlib import Path
import re
import stat
import sys
from dataclasses import dataclass


MAX_INPUT_BYTES = 1024 * 1024
MAX_NESTING = 16
SQL_CLIENTS = {"sqlite3", "psql", "mysql", "mariadb", "duckdb"}
SHELLS = {"sh", "bash", "dash", "zsh", "ksh"}


@dataclass
class Token:
    value: str
    raw: str
    kind: str = "word"
    start: int = -1
    end: int = -1


class ParseError(ValueError):
    pass


def _substitution(text, start, backtick=False):
    """Read a literal command substitution without evaluating it."""
    i = start
    depth = 1
    quote = None
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if backtick and ch == "`":
            return text[start:i], i + 1
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "(" and not backtick:
            depth += 1
        elif ch == ")" and not backtick:
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    raise ParseError("Unterminated command substitution")


def _tokenize(text):
    """Keep operators distinct from quoted data; collect executed substitutions.

    A small lexer is sufficient for the documented literal-command policy. It
    deliberately does not expand variables, globs, aliases, or shell functions.
    """
    tokens, substitutions, heredocs = [], [], []
    i = 0
    expect_heredoc = None
    while i < len(text):
        ch = text[i]
        if ch in " \t\r":
            i += 1
            continue
        if ch == "#":
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        if ch == "\n":
            i += 1
            # Here-doc bodies are input data, not a sequence of shell commands.
            for delimiter, strip_tabs, quoted, data_token in heredocs:
                body = []
                while i < len(text):
                    end = text.find("\n", i)
                    end = len(text) if end < 0 else end
                    line = text[i:end]
                    i = min(end + 1, len(text))
                    compared = line.lstrip("\t") if strip_tabs else line
                    if compared == delimiter:
                        break
                    body.append(line)
                else:
                    raise ParseError("Unterminated here-document")
                content = "\n".join(body)
                # Keep the body with its own redirect, even before a pipeline.
                data_token.value = data_token.raw = content
                if not quoted:
                    # Unquoted here-docs expand substitutions even inside quotes.
                    j = 0
                    while j < len(content):
                        if content[j] == "\\":
                            j += 2
                        elif content.startswith("$(", j):
                            sub, j = _substitution(content, j + 2)
                            substitutions.append(sub)
                        elif content[j] == "`":
                            sub, j = _substitution(content, j + 1, True)
                            substitutions.append(sub)
                        else:
                            j += 1
            heredocs = []
            tokens.append(Token("\n", "\n", "op"))
            continue
        if ch in ";&|()<>":
            op = ch
            if text[i:i + 3] in {"<<<", "<<-"}:
                op = text[i:i + 3]
            elif text[i:i + 2] in {"&&", "||", ">>", "<<", ";;", "|&", "&>", "<>", ">&", "<&", ">|"}:
                op = text[i:i + 2]
            tokens.append(Token(op, op, "op", i, i + len(op)))
            i += len(op)
            if op in {"<<", "<<-"}:
                expect_heredoc = op
            continue
        start, value, quote = i, [], None
        while i < len(text):
            ch = text[i]
            if quote is None and (ch.isspace() or ch in ";&|()<>"):
                break
            if ch == "\\" and quote != "'":
                if i + 1 >= len(text):
                    raise ParseError("Trailing shell escape")
                following = text[i + 1]
                if quote == '"' and following not in '$`"\\\n':
                    value.append("\\")
                    i += 1
                    continue
                if following != "\n":
                    value.append(following)
                i += 2
                continue
            if ch in "'\"" and (quote is None or quote == ch):
                quote = ch if quote is None else None
                i += 1
                continue
            if quote != "'" and text.startswith("$(", i):
                sub, end = _substitution(text, i + 2)
                substitutions.append(sub)
                value.append(text[i:end])
                i = end
                continue
            if quote != "'" and ch == "`":
                sub, end = _substitution(text, i + 1, True)
                substitutions.append(sub)
                value.append(text[i:end])
                i = end
                continue
            value.append(ch)
            i += 1
        if quote is not None:
            raise ParseError("Unterminated shell quote")
        token = Token("".join(value), text[start:i], "word", start, i)
        tokens.append(token)
        if expect_heredoc:
            data_token = Token("", "", "data")
            tokens.append(data_token)
            heredocs.append((token.value, expect_heredoc == "<<-", token.raw != token.value, data_token))
            expect_heredoc = None
    if expect_heredoc or heredocs:
        raise ParseError("Unterminated here-document")
    return tokens, substitutions


def _sql_reason(sql, dialect=None):
    """Ignore quoted values/comments and require WHERE at the DELETE's depth."""
    comments = r"#[^\n]*(?:\n|$)|" if dialect in {"mysql", "mariadb"} else ""
    pattern = re.compile(
        comments + r"\$(?P<tag>[A-Za-z_][A-Za-z_0-9]*|)\$.*?\$(?P=tag)\$|"
        r"--[^\n]*(?:\n|$)|/\*.*?\*/|'(?:''|\\.|[^'])*'|"
        r'"(?:""|[^\"])*"|`(?:``|[^`])*`|\[[^\]]*\]|'
        r"[A-Za-z_][A-Za-z_0-9$]*|[();]", re.S
    )
    statements, current, depth = [], [], 0
    for match in pattern.finditer(sql):
        word = match.group()
        if word.startswith(("--", "/*", "#", "$", "'", '"', "`", "[")):
            continue
        if word == ";":
            statements.append(current)
            current, depth = [], 0
            continue
        if word == ")":
            depth = max(0, depth - 1)
        current.append((word.upper(), depth))
        if word == "(":
            depth += 1
    statements.append(current)
    for statement in statements:
        for i, (word, level) in enumerate(statement):
            following = statement[i + 1][0] if i + 1 < len(statement) else None
            if word == "DROP" and (following == "TABLE" or
                                   (following == "TEMPORARY" and i + 2 < len(statement) and statement[i + 2][0] == "TABLE")):
                return "DROP TABLE removes a table and its data."
            if word == "TRUNCATE" and following != "(" and i == 0:
                return "TRUNCATE removes table contents."
            if word == "DELETE" and following == "FROM":
                tail = statement[i + 2:]
                # A WHERE in a nested SELECT, string, or comment is not a guard.
                if not any(w == "WHERE" and d == level for w, d in tail):
                    return "DELETE FROM without a WHERE clause removes all rows."
    return None


def _unwrap(words):
    """Skip common execution wrappers and their documented option arguments."""
    words = list(words)
    value_flags = {"-u", "-g", "-h", "-p", "-C", "--user", "--group",
                   "--host", "--prompt", "--chdir", "--unset"}
    while words:
        if re.match(r"^[A-Za-z_][A-Za-z_0-9]*=", words[0]):
            words.pop(0)
            continue
        name = os.path.basename(words[0])
        if name in {"then", "do", "else", "elif", "if", "while", "until", "!", "{"}:
            words.pop(0)
            continue
        if name not in {"sudo", "env", "command", "builtin", "exec", "nohup"}:
            break
        words.pop(0)
        while words and words[0].startswith("-"):
            flag = words.pop(0)
            if flag == "--":
                break
            if flag in value_flags and words:
                words.pop(0)
    return words


def _executable_words(tokens):
    """Redirect targets and adjacent file descriptors are not command names."""
    words = []
    skip_target = False
    for i, token in enumerate(tokens):
        if token.kind == "op" and token.value in {">", ">>", "<", "<<", "<<-", "<<<", "&>", "<>", ">&", "<&", ">|"}:
            if i and tokens[i - 1].value.isdigit() and tokens[i - 1].end == token.start and words:
                words.pop()
            skip_target = True
        elif token.kind == "word":
            if skip_target:
                skip_target = False
            else:
                words.append(token.value)
    return words


def _command_reason(tokens, upstream, nesting):
    raw_words = _executable_words(tokens)
    words = _unwrap(raw_words)
    if not words:
        return None
    name, args = os.path.basename(words[0]), words[1:]
    if name == "rm":
        recursive = force = False
        for arg in args:
            if arg == "--":
                break
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
            elif arg.startswith("-") and not arg.startswith("--"):
                recursive |= "r" in arg[1:] or "R" in arg[1:]
                force |= "f" in arg[1:]
        if recursive and force:
            return "Recursive forced removal (rm -rf) is blocked."
    if name == "git":
        remaining = list(args)
        while remaining and remaining[0].startswith("-"):
            flag = remaining.pop(0)
            if flag in {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"} and remaining:
                remaining.pop(0)
        if remaining and remaining.pop(0) == "push":
            option_mode = True
            while remaining:
                arg = remaining.pop(0)
                if arg == "--":
                    option_mode = False
                    continue
                if option_mode and arg in {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}:
                    if remaining:
                        remaining.pop(0)
                    continue
                if option_mode and (arg == "--force" or arg.startswith("--force=") or
                                    arg == "--force-with-lease" or arg.startswith("--force-with-lease=")):
                    return "Forced git push can overwrite remote history."
                if option_mode and re.fullmatch(r"-[vqufn]+", arg) and "f" in arg:
                    return "Forced git push can overwrite remote history."
                if arg.startswith("+"):
                    return "A '+' git push refspec forces a remote update."
    if name in SHELLS:
        for i, arg in enumerate(args):
            if arg == "--":
                break
            if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                if i + 1 < len(args):
                    return inspect_command(args[i + 1], nesting + 1)
                break
    if name.lower() in {"drop", "truncate", "delete", "with"}:
        reason = _sql_reason(" ".join(t.raw for t in tokens))
        if reason:
            return reason
    if name in SQL_CLIENTS:
        payloads = [t.value for t in tokens if t.kind == "data"]
        if name in {"sqlite3", "duckdb"}:
            payloads.extend(args)
        else:
            flags = {"-c", "--command"} if name == "psql" else {"-e", "--execute"}
            for i, arg in enumerate(args):
                if arg in flags and i + 1 < len(args):
                    payloads.append(args[i + 1])
                elif any(arg.startswith(flag + "=") for flag in flags if flag.startswith("--")):
                    payloads.append(arg.split("=", 1)[1])
                elif len(arg) > 2 and arg[:2] in flags:
                    payloads.append(arg[2:])
        # Here-strings and literal echo/printf pipelines also deliver SQL data.
        for i, token in enumerate(tokens[:-1]):
            if token.kind == "op" and token.value == "<<<":
                payloads.append(tokens[i + 1].value)
        payloads.extend(upstream)
        for payload in payloads:
            reason = _sql_reason(payload, name)
            if reason:
                return reason
    return None


def inspect_command(command, nesting=0):
    if nesting > MAX_NESTING:
        raise ParseError("Command nesting exceeds the inspection limit")
    tokens, substitutions = _tokenize(command)
    for sub in substitutions:
        reason = inspect_command(sub, nesting + 1)
        if reason:
            return reason
    segment, upstream = [], []
    for token in tokens + [Token(";", ";", "op")]:
        if token.kind == "op" and token.value in {";", ";;", "&&", "||", "|", "|&", "&", "\n", "(", ")"}:
            reason = _command_reason(segment, upstream, nesting)
            if reason:
                return reason
            words = _unwrap(_executable_words(segment))
            upstream = []
            if token.value in {"|", "|&"} and words:
                if os.path.basename(words[0]) == "echo":
                    upstream = [" ".join(words[1:])]
                elif os.path.basename(words[0]) == "printf":
                    # Inspect complete SQL arguments; do not evaluate formats.
                    upstream = words[1:]
            segment = []
        else:
            segment.append(token)
    return None


def _write_audit(command, project_path, reason):
    """Append one private JSON record. Never follow a log-file symlink."""
    directory = Path.home() / ".claude" / "hooks"
    for path in (directory.parent, directory):
        if path.is_symlink():
            raise OSError("Audit directory must not be a symlink")
        path.mkdir(mode=0o700, exist_ok=True)
        if not path.is_dir():
            raise OSError("Audit path must be a directory")
    record = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "reason": reason,
    }
    data = (json.dumps(record, ensure_ascii=True) + "\n").encode("utf-8")
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    fd = os.open(str(directory / "blocked.log"), flags, 0o600)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise OSError("Audit log must be a regular, unshared file")
        os.fchmod(fd, 0o600)
        # Serialize append writes so concurrent hooks cannot interleave records.
        import fcntl
        fcntl.flock(fd, fcntl.LOCK_EX)
        while data:
            written = os.write(fd, data)
            if written <= 0:
                raise OSError("Audit append did not complete")
            data = data[written:]
    finally:
        os.close(fd)


def main():
    command, project_path = "[invalid hook input]", os.getcwd()
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            raise ValueError("Hook input exceeds 1 MiB")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError("Hook input must be a JSON object")
        if event.get("hook_event_name", "PreToolUse") != "PreToolUse":
            return 0
        if "tool_name" not in event:
            raise ValueError("Hook input is missing tool_name")
        if event["tool_name"] != "Bash":
            return 0
        tool_input = event.get("tool_input")
        if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
            raise ValueError("Bash tool input must contain a string command")
        command = tool_input["command"]
        cwd = event.get("cwd", project_path)
        if not isinstance(cwd, str):
            raise ValueError("Hook cwd must be a string")
        project_path = cwd
        reason = inspect_command(command)
        if reason is None:
            return 0
    except (ValueError, UnicodeError, RecursionError) as exc:
        reason = "Cannot safely inspect the hook input: " + str(exc)
    message = "Blocked by destructive-command guard: " + reason
    try:
        _write_audit(command, project_path, reason)
    except (OSError, ValueError) as exc:
        # Audit failure must never turn a denial into permission to execute.
        message += " Audit logging failed (" + type(exc).__name__ + "); command remains blocked."
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
