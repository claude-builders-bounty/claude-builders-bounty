#!/usr/bin/env python3
"""A conservative pattern guard for Claude Code's PreToolUse/Bash hook.

This inspects command text; it never executes it. It is not a shell sandbox.
"""

import datetime
import json
import os
import re
import stat
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Token:
    value: str
    kind: str = "word"
    raw: str = ""
    quoted: bool = False


class InspectionError(ValueError):
    pass


def substitution(text, start, backtick=False):
    """Return the body and end position of an executable shell substitution."""
    i = start + (1 if backtick else 2)
    begin, depth, quote = i, 1, None
    while i < len(text):
        c = text[i]
        if c == "\\" and quote != "'":
            i += 2
            continue
        if backtick and c == "`":
            return text[begin:i], i + 1
        if quote:
            if c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif not backtick:
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    return text[begin:i], i + 1
        i += 1
    raise InspectionError("Unterminated command substitution; cannot inspect safely.")


def heredoc_expansions(body):
    """Quotes in an unquoted here-document do not suppress substitutions."""
    found, i = [], 0
    while i < len(body):
        if body[i] == "\\":
            i += 2
        elif body.startswith("$(", i) or body[i] == "`":
            value, i = substitution(body, i, body[i] == "`")
            found.append(value)
        else:
            i += 1
    return found


def shell_tokens(text):
    """Tokenize literal commands, keeping operators distinct from quoted data."""
    tokens, expansions, pending = [], [], []
    value, raw = [], []
    quote, quoted, active, expect_here = None, False, False, None
    i = 0

    def flush():
        nonlocal value, raw, quoted, active, expect_here
        if active:
            word = Token("".join(value), raw="".join(raw), quoted=quoted)
            tokens.append(word)
            if expect_here is not None:
                placeholder = Token("", kind="here", quoted=quoted)
                tokens.append(placeholder)
                pending.append((word.value, expect_here, placeholder))
                expect_here = None
        value, raw, quoted, active = [], [], False, False

    while i < len(text):
        c = text[i]
        if quote == "'":
            raw.append(c)
            if c == quote:
                quote = None
            else:
                value.append(c)
            i += 1
            continue
        if c == "\\":
            if i + 1 >= len(text):
                raise InspectionError("Trailing shell escape; cannot inspect safely.")
            following = text[i + 1]
            # Inside double quotes, only these characters are escaped by Bash.
            if quote == '"' and following not in '$`"\\\n':
                value.append(c)
                raw.append(c)
                i += 1
                continue
            raw.extend((c, following))
            if following != "\n":
                value.append(following)
                active = True
                quoted = True
            i += 2
            continue
        if text.startswith("$(", i) or c == "`":
            body, end = substitution(text, i, c == "`")
            expansions.append(body)
            raw.append(text[i:end])
            value.append("<substitution>")
            active = True
            i = end
            continue
        if quote == '"':
            raw.append(c)
            if c == quote:
                quote = None
            else:
                value.append(c)
            i += 1
            continue
        if c in "\"'":
            quote, quoted, active = c, True, True
            raw.append(c)
            i += 1
            continue
        if c == "#" and not active:
            end = text.find("\n", i)
            i = len(text) if end < 0 else end
            continue
        if c in " \t\r":
            flush()
            i += 1
            continue
        if c == "\n":
            flush()
            i += 1
            for delimiter, strip_tabs, placeholder in pending:
                lines = []
                while i < len(text):
                    end = text.find("\n", i)
                    end = len(text) if end < 0 else end + 1
                    line = text[i:end]
                    i = end
                    candidate = line.lstrip("\t") if strip_tabs else line
                    if candidate.rstrip("\r\n") == delimiter:
                        break
                    lines.append(candidate)
                else:
                    raise InspectionError("Unterminated here-document; cannot inspect safely.")
                placeholder.value = "".join(lines)
                if not placeholder.quoted:
                    expansions.extend(heredoc_expansions(placeholder.value))
            pending.clear()
            tokens.append(Token("\n", kind="op"))
            continue
        if c in ";&|()<>":
            # A directly attached, unquoted fd prefix is not the command name.
            if c in "<>" and active and not quoted and "".join(value).isdigit():
                value, raw, active = [], [], False
            flush()
            operator = c
            if text[i:i + 3] in ("<<-", "<<<"):
                operator = text[i:i + 3]
            elif text[i:i + 2] in ("&&", "||", "<<", ">>", "|&", ";;", "<&", ">&"):
                operator = text[i:i + 2]
            tokens.append(Token(operator, kind="op"))
            if operator in ("<<", "<<-"):
                expect_here = operator == "<<-"
            i += len(operator)
            continue
        value.append(c)
        raw.append(c)
        active = True
        i += 1
    flush()
    if quote or pending or expect_here is not None:
        raise InspectionError("Incomplete shell syntax; cannot inspect safely.")
    return tokens, expansions


SQL_TOKEN = re.compile(
    r"--[^\n]*|\#[^\n]*|/\*[\s\S]*?\*/|"
    r"'(?:''|\\.|[^'\\])*'|\"(?:\"\"|[^\"])*\"|"
    r"`(?:``|[^`])*`|\[(?:\]\]|[^\]])*\]|"
    r"\$(?:[A-Za-z_][A-Za-z_0-9]*)?\$|[A-Za-z_][A-Za-z_0-9]*|[();]",
    re.MULTILINE,
)


def sql_reason(sql):
    words, cursor = [], 0
    while True:
        match = SQL_TOKEN.search(sql, cursor)
        if match is None:
            break
        token = match.group()
        cursor = match.end()
        if token.startswith(("--", "#")):
            continue
        if token.startswith("/*"):
            executable = re.match(r"/\*(?:!|M!)\d*\s*", token)
            if executable:
                # MySQL/MariaDB version comments contain executable SQL.
                sql = sql[:match.start()] + token[executable.end():-2] + sql[match.end():]
                cursor = match.start()
            else:
                # PostgreSQL permits nested block comments.
                level, end = 1, match.start() + 2
                while level:
                    delimiter = re.search(r"/\*|\*/", sql[end:])
                    if delimiter is None:
                        raise InspectionError("Unterminated SQL block comment.")
                    level += 1 if delimiter.group() == "/*" else -1
                    end += delimiter.end()
                cursor = end
            continue
        if token.startswith("$"):
            end = sql.find(token, cursor)
            if end < 0:
                raise InspectionError("Unterminated SQL dollar string.")
            cursor = end + len(token)
            words.append("<literal>")
        elif token[0] in "'\"`[":
            words.append("<literal>")
        else:
            words.append(token.upper())
    depth = 0
    for i, word in enumerate(words):
        if word == "(":
            depth += 1
        elif word == ")":
            depth -= 1
        elif word == "DROP" and words[i + 1:i + 2] == ["TABLE"]:
            return "DROP TABLE removes a table and its data."
        elif (word == "TRUNCATE" and (i == 0 or words[i - 1] in (";", "("))
              and words[i + 1:i + 2] != ["("]):
            return "TRUNCATE removes all rows from a table."
        elif word == "DELETE" and words[i + 1:i + 2] == ["FROM"]:
            level, filtered = depth, False
            for following in words[i + 2:]:
                if following == "(":
                    level += 1
                elif following == ")":
                    level -= 1
                    if level < depth:
                        break
                elif following == ";":
                    break
                elif following == "WHERE" and level == depth:
                    filtered = True
            if not filtered:
                return "DELETE FROM has no WHERE clause in that deletion statement."
    return None


ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z_0-9]*=.*", re.DOTALL)
SHELLS = {"sh", "bash", "dash", "zsh", "ksh"}
SQL_CLIENTS = {"psql", "pgcli", "mysql", "mariadb", "sqlite3", "duckdb"}


def unwrap(words):
    words = list(words)
    while words:
        if ASSIGNMENT.fullmatch(words[0]) or words[0] in ("if", "then", "elif", "else", "do", "!", "{"):
            words.pop(0)
            continue
        name = os.path.basename(words[0])
        takes_value = {
            "sudo": {"-u", "-g", "-h", "-p", "-C", "-T", "--user", "--group", "--host", "--prompt", "--chdir"},
            "env": {"-u", "--unset", "-C", "--chdir"},
            "nice": {"-n", "--adjustment"},
            "command": set(), "builtin": set(), "exec": {"-a"}, "time": {"-f", "-o", "--format", "--output"},
        }
        if name not in takes_value:
            break
        if name == "command":
            for option in words[1:]:
                if not option.startswith("-") or option == "--":
                    break
                if "v" in option or "V" in option:
                    return []  # command -v/-V looks up names; it does not run them.
        words.pop(0)
        while words and words[0].startswith("-"):
            option = words.pop(0)
            if option == "--":
                break
            if option in takes_value[name] and words:
                words.pop(0)
    return words


def literal_printf(args):
    """Evaluate the common literal %s/%% formats without invoking a shell."""
    if not args:
        return ""
    template, values = args[0], list(args[1:])
    # Unsupported formatting is outside literal pipeline inspection.
    if re.search(r"%(?!s|%)", template):
        return None
    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", "a": "\a", "b": "\b"}
    template = re.sub(r"\\([nrt\\ab])", lambda m: escapes[m[1]], template)
    output = []
    while True:
        i, consumed = 0, 0
        while i < len(template):
            if template[i:i + 2] == "%%":
                output.append("%")
                i += 2
            elif template[i:i + 2] == "%s":
                output.append(values.pop(0) if values else "")
                consumed += 1
                i += 2
            else:
                output.append(template[i])
                i += 1
        if not values or consumed == 0:
            return "".join(output)


def command_reason(tokens, piped, depth):
    words, here, raw_words = [], [], []
    skip_redirection = False
    for token in tokens:
        if token.kind == "here":
            here.append(token.value)
        elif token.kind == "op":
            skip_redirection = token.value in ("<", ">", ">>", "<<", "<<-", "<&", ">&")
            if token.value == "<<<":
                skip_redirection = "string"
        elif skip_redirection:
            if skip_redirection == "string":
                here.append(token.value + "\n")
            skip_redirection = False
        else:
            words.append(token.value)
            raw_words.append(token.raw)
    words = unwrap(words)
    if not words:
        return None, "".join(here)
    name, args = os.path.basename(words[0]), words[1:]
    if name == "rm":
        recursive = force = False
        for arg in args:
            if arg == "--":
                break
            if arg.startswith("--"):
                recursive |= arg == "--recursive"
                force |= arg == "--force"
            elif arg.startswith("-"):
                recursive |= "r" in arg or "R" in arg
                force |= "f" in arg
        if recursive and force:
            return "rm combines recursive and force deletion.", None
    if name == "git":
        pos = 0
        while pos < len(args) and args[pos].startswith("-"):
            option = args[pos]
            pos += 2 if option in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env") else 1
        if args[pos:pos + 1] == ["push"]:
            options = True
            for arg in args[pos + 1:]:
                if arg == "--":
                    options = False
                elif (options and (arg.split("=", 1)[0] in ("--force", "--force-with-lease")
                                   or (arg.startswith("-") and not arg.startswith("--") and "f" in arg))) or arg.startswith("+"):
                    return "git push requests a forced update of remote history.", None
    incoming = ([piped] if piped is not None else []) + here
    if name in SHELLS:
        scripts = list(incoming)
        for i, arg in enumerate(args):
            if arg.startswith("-") and not arg.startswith("--") and "c" in arg:
                if i + 1 < len(args):
                    scripts.append(args[i + 1])
                break
        for script in scripts:
            reason = inspect(script, depth + 1)
            if reason:
                return reason, None
    if name in SQL_CLIENTS:
        sql = list(incoming)
        for i, arg in enumerate(args):
            if arg in ("-c", "--command", "-e", "--execute", "-cmd") and i + 1 < len(args):
                sql.append(args[i + 1])
            elif arg.startswith(("--command=", "--execute=")):
                sql.append(arg.split("=", 1)[1])
            elif ((name in ("psql", "pgcli") and arg.startswith("-c")) or
                  (name in ("mysql", "mariadb") and arg.startswith("-e"))) and len(arg) > 2:
                sql.append(arg[2:])
        if name in ("sqlite3", "duckdb"):
            # SQL passed positionally after the database name is also executable.
            sql.extend(arg for arg in args if re.search(r"\b(?:DROP|TRUNCATE|DELETE)\b", arg, re.I))
        for statement in sql:
            reason = sql_reason(statement)
            if reason:
                return reason, None
    if name.upper() in ("DROP", "TRUNCATE", "DELETE"):
        return sql_reason(" ".join(raw_words)), None
    if name == "printf":
        return None, literal_printf(args)
    if name == "echo":
        while args and re.fullmatch(r"-[nE]+", args[0]):
            args = args[1:]
        return None, " ".join(args) + "\n"
    if name == "cat" and here:
        return None, "".join(here)
    return None, None


def inspect(command, depth=0):
    if depth > 12:
        raise InspectionError("Command nesting exceeds the inspection limit.")
    tokens, expansions = shell_tokens(command)
    for expansion in expansions:
        reason = inspect(expansion, depth + 1)
        if reason:
            return reason
    current, piped = [], None
    for token in tokens + [Token("\n", kind="op")]:
        if token.kind == "op" and token.value in (";", ";;", "&", "&&", "||", "|", "|&", "\n", "(", ")"):
            reason, output = command_reason(current, piped, depth)
            if reason:
                return reason
            piped = output if token.value in ("|", "|&") else None
            current = []
        else:
            current.append(token)
    return None


def audit(command, project, reason):
    directory = Path.home() / ".claude" / "hooks"
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    flags = (os.O_WRONLY | os.O_APPEND | os.O_CREAT
             | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
    fd = os.open(str(directory / "blocked.log"), flags, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError("Audit path is not a regular file")
        record = {"timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  "command": command, "project_path": project, "reason": reason}
        data = (json.dumps(record, ensure_ascii=True) + "\n").encode("utf-8")
        if os.write(fd, data) != len(data):
            raise OSError("Incomplete audit write")
    finally:
        os.close(fd)


def main():
    command, project = "<invalid hook input>", os.getcwd()
    try:
        raw = sys.stdin.read(1_048_577)
        if len(raw) > 1_048_576:
            raise InspectionError("Hook input exceeds 1 MiB.")
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise InspectionError("Hook input must be a JSON object.")
        if event.get("hook_event_name", "PreToolUse") != "PreToolUse":
            return 0
        if event.get("tool_name") != "Bash":
            return 0
        details = event.get("tool_input")
        if not isinstance(details, dict) or not isinstance(details.get("command"), str):
            raise InspectionError("Bash hook input is missing a command string.")
        command = details["command"]
        if isinstance(event.get("cwd"), str):
            project = event["cwd"]
        reason = inspect(command)
    except (ValueError, RecursionError) as exc:
        reason = "Cannot inspect this command: " + str(exc)
    if not reason:
        return 0
    try:
        audit(command, project, reason)
    except OSError as exc:
        print("Audit log unavailable (command remains blocked): " + str(exc), file=sys.stderr)
    print("Destructive command blocked: " + reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
