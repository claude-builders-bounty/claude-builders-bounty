#!/usr/bin/env python3
"""Conservative, stdlib-only Claude Code PreToolUse guard for Bash commands."""

from __future__ import annotations

import json
import os
import re
import shlex
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


MAX_INPUT_BYTES = 64 * 1024
MAX_COMMAND_CHARS = 8 * 1024
MAX_LOG_BYTES = 1024 * 1024
MAX_LOG_COMMAND_CHARS = 512
MAX_PROJECT_CHARS = 512

BLOCKED_MESSAGES = {
    "rm": "Blocked recursive forced removal (rm -r/-R with -f/--force). Review the target and use a narrower command.",
    "git": "Blocked forced git push. Review the remote and use a normal push or an explicit, deliberate recovery plan.",
    "sql-drop": "Blocked SQL DROP TABLE statement. Review the target database and use an explicit recovery plan.",
    "sql-truncate": "Blocked SQL TRUNCATE statement. Review the target database and use an explicit recovery plan.",
    "sql-delete": "Blocked SQL DELETE FROM without an outer WHERE clause. Add a restrictive WHERE clause after reviewing the target rows.",
    "sql-stdin": "Blocked SQL input from a stdin source that could not be statically checked. Use a direct SQL argument or a simple literal input and review it.",
    "input": "Safety hook could not validate the Bash input, so the command was blocked. Check the hook input and retry.",
    "analysis": "Safety hook could not complete command analysis, so the command was blocked. Check the hook and retry.",
}

WRAPPERS = {"sudo", "doas", "command", "builtin", "exec", "env", "nohup", "time"}
SHELLS = {"sh", "bash", "dash", "zsh", "ksh", "ash"}
SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "sqlcmd", "duckdb"}


def split_shell_commands(script: str) -> list[str]:
    """Split on unquoted shell control operators without evaluating anything."""
    commands: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(script):
        ch = script[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if quote:
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        # A shell comment starts at the beginning of a word. Preserve the
        # newline as a command separator.
        if ch == "#" and (i == 0 or script[i - 1].isspace() or script[i - 1] in ";|&"):
            nl = script.find("\n", i)
            if nl == -1:
                commands.append(script[start:i])
                return [c for c in commands if c.strip()]
            commands.append(script[start:i])
            start = nl + 1
            i = nl + 1
            continue
        if ch in ";\n|&":
            commands.append(script[start:i])
            if ch in "|&" and i + 1 < len(script) and script[i + 1] == ch:
                i += 2
            elif ch == "|" and i + 1 < len(script) and script[i + 1] == "&":
                i += 2
            else:
                i += 1
            start = i
            continue
        i += 1
    commands.append(script[start:])
    return [c for c in commands if c.strip()]


def split_shell_groups(script: str) -> list[list[str]]:
    """Group simple command segments joined by a pipeline, respecting quotes/comments."""
    groups: list[list[str]] = []
    current_group: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    i = 0

    def add_segment(end: int) -> None:
        nonlocal start
        segment = script[start:end].strip()
        if segment:
            current_group.append(segment)

    def finish_group() -> None:
        nonlocal current_group
        if current_group:
            groups.append(current_group)
        current_group = []

    while i < len(script):
        ch = script[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if quote:
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            continue
        if ch == "#" and (i == 0 or script[i - 1].isspace() or script[i - 1] in ";|&"):
            nl = script.find("\n", i)
            if nl == -1:
                add_segment(i)
                finish_group()
                return groups
            add_segment(i)
            finish_group()
            start = nl + 1
            i = nl + 1
            continue
        if ch in ";\n|&":
            add_segment(i)
            if ch == "|" and not (i + 1 < len(script) and script[i + 1] == "|"):
                if i + 1 < len(script) and script[i + 1] == "&":
                    i += 2
                else:
                    i += 1
                start = i
                continue
            if ch in "|&" and i + 1 < len(script) and script[i + 1] == ch:
                i += 2
            else:
                i += 1
            finish_group()
            start = i
            continue
        i += 1
    add_segment(len(script))
    finish_group()
    return groups


def heredoc_bodies(script: str) -> list[str]:
    return [str(entry["body"]) for entry in heredoc_entries(script)]


def heredoc_entries(script: str) -> list[dict[str, object]]:
    """Extract here-docs with their header, body span, and quoted status."""
    header = re.compile(
        r"<<(?P<dash>-?)[ \t]*(?P<quote>['\"]?)(?P<delimiter>[A-Za-z_][A-Za-z0-9_]*)(?P=quote)(?=[ \t;|&<>]|$)"
    )

    def headers_outside_quotes(line: str) -> list[re.Match[str]]:
        found: list[re.Match[str]] = []
        quote: str | None = None
        escaped = False
        i = 0
        while i < len(line):
            ch = line[i]
            if escaped:
                escaped = False
                i += 1
                continue
            if quote == "'":
                if ch == "'":
                    quote = None
                i += 1
                continue
            if ch == "\\" and quote != "'":
                escaped = True
                i += 1
                continue
            if quote:
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ("'", '"'):
                quote = ch
                i += 1
                continue
            if ch == "#" and (i == 0 or line[i - 1].isspace() or line[i - 1] in ";|&"):
                break
            if line.startswith("<<", i) and not line.startswith("<<<", i):
                match = header.match(line, i)
                if match:
                    found.append(match)
                    i = match.end()
                    continue
            i += 1
        return found

    lines = script.splitlines(keepends=True)
    starts: list[int] = []
    total = 0
    for line in lines:
        starts.append(total)
        total += len(line)
    entries: list[dict[str, object]] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        content = line.rstrip("\r\n")
        matches = headers_outside_quotes(content)
        if not matches:
            index += 1
            continue
        consume_index = index + 1
        for match in matches:
            delimiter = match.group("delimiter")
            body_start = starts[consume_index] if consume_index < len(starts) else len(script)
            body_lines: list[str] = []
            j = consume_index
            found = False
            while j < len(lines):
                candidate = lines[j]
                candidate_text = candidate.rstrip("\r\n")
                check = candidate_text.lstrip("\t") if match.group("dash") else candidate_text
                if check == delimiter:
                    body_end = starts[j] + len(candidate)
                    entries.append({
                        "body": "".join(body_lines),
                        "quoted": bool(match.group("quote")),
                        "header": content,
                        "body_start": body_start,
                        "body_end": body_end,
                    })
                    consume_index = j + 1
                    found = True
                    break
                body_lines.append(candidate)
                j += 1
            if not found:
                entries.append({
                    "body": "".join(body_lines),
                    "quoted": bool(match.group("quote")),
                    "header": content,
                    "body_start": body_start,
                    "body_end": len(script),
                })
                consume_index = len(lines)
                break
        index = consume_index
    return entries


def mask_heredoc_bodies(script: str, entries: list[dict[str, object]]) -> str:
    chars = list(script)
    for entry in entries:
        for index in range(int(entry["body_start"]), int(entry["body_end"])):
            if chars[index] not in "\r\n":
                chars[index] = " "
    return "".join(chars)


def has_shell_expansion(text: str) -> bool:
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if ch in ("'", '"'):
            quote = None if quote == ch else (ch if quote is None else quote)
            i += 1
            continue
        if ch == "`" or (ch == "$" and i + 1 < len(text) and (text[i + 1] in "({" or text[i + 1].isalpha() or text[i + 1] == "_")):
            return True
        i += 1
    return False


def has_stdin_redirection(text: str, allow_heredoc: bool = False) -> bool:
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(text):
        ch = text[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if ch in ("'", '"'):
            quote = None if quote == ch else (ch if quote is None else quote)
            i += 1
            continue
        if ch == "<":
            if allow_heredoc and text[i:i + 2] == "<<" and text[i:i + 3] != "<<<":
                i += 2
                continue
            return True
        i += 1
    return False


def printf_sql_text(words: list[str]) -> str | None:
    """Expand only static printf %%s/%%%% formats; return None if ambiguous."""
    if len(words) < 2:
        return ""
    fmt = words[1]
    if fmt.startswith("-") or "\\" in fmt:
        return None
    args = words[2:]
    arg_index = 0
    output: list[str] = []
    i = 0
    while i < len(fmt):
        if fmt[i] != "%":
            output.append(fmt[i])
            i += 1
            continue
        if i + 1 >= len(fmt):
            return None
        spec = fmt[i + 1]
        if spec == "%":
            output.append("%")
        elif spec == "s":
            if arg_index < len(args):
                output.append(args[arg_index])
                arg_index += 1
        else:
            return None
        i += 2
    if arg_index < len(args):
        # Bash printf repeats the format for remaining arguments. This narrow
        # scanner declines to emulate the repetition rather than miss SQL.
        return None
    return "".join(output)


def shell_reads_stdin_as_script(words: list[str]) -> bool:
    """Whether a known shell's arguments leave stdin as its script source."""
    i = 1
    while i < len(words):
        word = words[i]
        if word in ("-c", "--command") or (word.startswith("-") and "c" in word[1:] and not word.startswith("--")):
            return False
        if word == "-s":
            return True
        if word == "--":
            return True
        if word in ("<<", "<<-"):
            i += 2  # heredoc operator and its delimiter
            continue
        if word.startswith(("<<", "<<<")):
            i += 1
            continue
        if word.startswith("-"):
            i += 1
            continue
        return False  # A script file or command operand was supplied.
    return True


def extract_substitutions(script: str) -> list[str]:
    """Return command substitutions/backticks, skipping literal single quotes."""
    found: list[str] = []
    quote: str | None = None
    escaped = False
    i = 0
    while i < len(script):
        ch = script[i]
        if escaped:
            escaped = False
            i += 1
            continue
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\" and quote != "'":
            escaped = True
            i += 1
            continue
        if ch == "'" and quote is None:
            quote = "'"
            i += 1
            continue
        if ch == '"':
            quote = None if quote == '"' else ('"' if quote is None else quote)
            i += 1
            continue
        if quote is None and ch == "#" and (i == 0 or script[i - 1].isspace() or script[i - 1] in ";|&"):
            nl = script.find("\n", i)
            if nl == -1:
                break
            i = nl + 1
            continue
        if ch == "`":
            end = i + 1
            body: list[str] = []
            escaped_inner = False
            while end < len(script):
                cur = script[end]
                if escaped_inner:
                    body.append(cur)
                    escaped_inner = False
                elif cur == "\\":
                    escaped_inner = True
                elif cur == "`":
                    break
                else:
                    body.append(cur)
                end += 1
            if end < len(script):
                found.append("".join(body))
                i = end + 1
                continue
        if ch == "$" and i + 1 < len(script) and script[i + 1] == "(":
            depth = 1
            j = i + 2
            inner_quote: str | None = None
            inner_escape = False
            while j < len(script) and depth:
                cur = script[j]
                if inner_escape:
                    inner_escape = False
                elif cur == "\\" and inner_quote != "'":
                    inner_escape = True
                elif inner_quote == "'":
                    if cur == "'":
                        inner_quote = None
                elif cur in ("'", '"'):
                    inner_quote = cur
                elif cur == "(":
                    depth += 1
                elif cur == ")":
                    depth -= 1
                j += 1
            if depth == 0:
                found.append(script[i + 2 : j - 1])
                i = j
                continue
        if quote is None and ch in ("'", '"'):
            quote = ch
        i += 1
    return found


def has_active_dollar_quote(segment: str) -> bool:
    """Detect Bash-only dollar quotes unsupported by Python shlex."""
    quote: str | None = None
    escaped = False
    for index, char in enumerate(segment):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote != "'":
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = None
            continue
        if char == "$" and index + 1 < len(segment) and segment[index + 1] in ("'", '"'):
            return True
        if char in ("'", '"'):
            quote = char
    return False


def shell_words(segment: str) -> list[str]:
    # Remove leading grouping punctuation so `(rm -rf x)` is checked like rm.
    segment = segment.strip()
    if has_active_dollar_quote(segment):
        # shlex drops the quote but keeps '$', potentially concealing rm/git/SQL.
        raise ValueError("unsupported Bash dollar quoting")
    while segment.startswith(("(", "{", "!")):
        segment = segment[1:].lstrip()
    try:
        return shlex.split(segment, comments=False, posix=True)
    except ValueError:
        # An unmatched quote means the parser cannot reliably identify the
        # command. The caller treats this as an analysis failure and blocks.
        raise


def unwrap_command(words: list[str]) -> list[str]:
    """Skip a small set of transparent launchers; do not interpret arbitrary shell syntax."""
    i = 0
    while i < len(words):
        head = os.path.basename(words[i]).lower()
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[i]):
            i += 1
            continue
        if head in ("if", "then", "else", "elif", "while", "until", "do", "!", "{"):
            i += 1
            continue
        if head not in WRAPPERS:
            break
        i += 1
        if head == "env":
            while i < len(words) and (words[i].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[i])):
                if words[i] in ("-u", "--unset", "-C", "--chdir") and i + 1 < len(words):
                    i += 2
                else:
                    i += 1
        elif head in ("sudo", "doas"):
            while i < len(words) and words[i].startswith("-"):
                if words[i] in ("-u", "-g", "-h", "-p", "-C", "-D") and i + 1 < len(words):
                    i += 2
                else:
                    i += 1
        elif head == "command" and i < len(words) and words[i] in ("-v", "-V", "-p"):
            i += 1
    return words[i:]


def detect_rm(words: list[str]) -> str | None:
    words = unwrap_command(words)
    if not words or os.path.basename(words[0]).lower() != "rm":
        return None
    recursive = False
    force = False
    for word in words[1:]:
        if word == "--":
            break
        if word == "--recursive":
            recursive = True
        elif word == "--force":
            force = True
        elif word.startswith("-") and not word.startswith("--"):
            flags = word[1:]
            recursive |= "r" in flags or "R" in flags
            force |= "f" in flags
    return "rm" if recursive and force else None


def detect_git_force_push(words: list[str]) -> str | None:
    words = unwrap_command(words)
    if not words or os.path.basename(words[0]).lower() != "git":
        return None
    i = 1
    global_value_options = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--exec-path"}
    while i < len(words):
        word = words[i]
        if word in global_value_options:
            i += 2
        elif word.startswith(("--git-dir=", "--work-tree=", "--namespace=", "--super-prefix=", "--exec-path=")):
            i += 1
        elif word in ("--no-pager", "--bare", "--literal-pathspecs", "--no-optional-locks"):
            i += 1
        else:
            break
    if i >= len(words) or words[i] != "push":
        return None
    for word in words[i + 1 :]:
        if (
            word in ("--force", "-f", "--force-with-lease")
            or word.startswith("--force-with-lease=")
            or (word.startswith("-") and not word.startswith("--") and "f" in word[1:])
            or (word.startswith("+") and len(word) > 1)
        ):
            return "git"
    return None


def sql_tokens(sql: str) -> list[str]:
    """Tokenize enough SQL to ignore comments, quoted strings, and nested WHEREs."""
    result: list[str] = []
    i = 0
    depth = 0
    word: list[str] = []

    def flush() -> None:
        if word:
            result.append("".join(word).upper())
            word.clear()

    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if ch == "-" and nxt == "-":
            flush()
            i += 2
            while i < len(sql) and sql[i] not in "\r\n":
                i += 1
            continue
        if ch == "/" and nxt == "*":
            flush()
            i += 2
            comment_depth = 1
            while i < len(sql) and comment_depth:
                if sql[i : i + 2] == "/*":
                    comment_depth += 1
                    i += 2
                elif sql[i : i + 2] == "*/":
                    comment_depth -= 1
                    i += 2
                else:
                    i += 1
            continue
        if ch == "#":
            flush()
            i += 1
            while i < len(sql) and sql[i] not in "\r\n":
                i += 1
            continue
        if ch == "$":
            dollar_tag = re.match(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$", sql[i:])
            if dollar_tag:
                flush()
                marker = dollar_tag.group(0)
                end = sql.find(marker, i + len(marker))
                i = len(sql) if end == -1 else end + len(marker)
                continue
        if ch in ("'", '"', "`", "["):
            flush()
            closing = "]" if ch == "[" else ch
            i += 1
            while i < len(sql):
                if sql[i] == closing:
                    if i + 1 < len(sql) and sql[i + 1] == closing:
                        i += 2
                        continue
                    i += 1
                    break
                if sql[i] == "\\" and i + 1 < len(sql):
                    i += 2
                else:
                    i += 1
            continue
        if ch == "(" and not (nxt.isalpha() or nxt.isdigit()):
            flush()
            depth += 1
            result.append("(")
            i += 1
            continue
        if ch == "(":
            flush()
            depth += 1
            result.append("(")
            i += 1
            continue
        if ch == ")":
            flush()
            depth = max(0, depth - 1)
            result.append(")")
            i += 1
            continue
        if ch == ";":
            flush()
            result.append(";")
            i += 1
            continue
        if ch.isalnum() or ch in "_$":
            word.append(ch)
        else:
            flush()
        i += 1
    flush()
    return result


def detect_sql(sql: str) -> str | None:
    tokens = sql_tokens(sql)
    statements: list[list[str]] = [[]]
    for token in tokens:
        if token == ";":
            statements.append([])
        else:
            statements[-1].append(token)
    for statement in statements:
        depth = 0
        annotated: list[tuple[str, int]] = []
        for token in statement:
            if token == "(":
                annotated.append((token, depth))
                depth += 1
            elif token == ")":
                depth = max(0, depth - 1)
                annotated.append((token, depth))
            else:
                annotated.append((token, depth))
        for index, (token, token_depth) in enumerate(annotated):
            next_word = annotated[index + 1][0] if index + 1 < len(annotated) else ""
            if token == "DROP" and next_word == "TABLE":
                return "sql-drop"
            if token == "TRUNCATE":
                return "sql-truncate"
            if token == "DELETE" and next_word == "FROM" and annotated[index + 1][1] == token_depth:
                has_where = False
                for later, later_depth in annotated[index + 2 :]:
                    # A closed CTE or subquery ends this DELETE's scope; a
                    # sibling WHERE must not qualify it.
                    if later == ")" and later_depth < token_depth:
                        break
                    if later == "WHERE" and later_depth == token_depth:
                        has_where = True
                        break
                if not has_where:
                    return "sql-delete"
    return None


def extract_sql(words: list[str]) -> list[str]:
    words = unwrap_command(words)
    if not words or os.path.basename(words[0]).lower() not in SQL_CLIENTS:
        return []
    client = os.path.basename(words[0]).lower()
    sql: list[str] = []
    i = 1
    while i < len(words):
        word = words[i]
        low = word.lower()
        if low in ("-c", "-e", "-q", "--command", "--execute", "--query", "-cmd"):
            if i + 1 < len(words):
                sql.append(words[i + 1])
                i += 2
                continue
        if low.startswith(("--command=", "--execute=", "--query=", "-cmd=")):
            sql.append(word.split("=", 1)[1])
        elif len(word) > 2 and word[:2] in ("-c", "-e", "-Q"):
            sql.append(word[2:])
        i += 1
    if client == "sqlite3" and not sql:
        positional = [w for w in words[1:] if not w.startswith("-")]
        if len(positional) >= 2:
            sql.append(" ".join(positional[1:]))
    return sql


def inspect_sql_pipelines(script: str) -> str | None:
    """Check known SQL client stdin sources; fail closed on dynamic sources."""
    entries = heredoc_entries(script)
    masked = mask_heredoc_bodies(script, entries)
    groups = split_shell_groups(masked)

    # Inspect only here-documents attached to a pipeline or command that invokes
    # a recognized SQL client. A quoted delimiter makes the body literal data.
    for entry in entries:
        for header_group in split_shell_groups(str(entry["header"])):
            clients = []
            for segment in header_group:
                words = unwrap_command(shell_words(segment))
                if words and os.path.basename(words[0]).lower() in SQL_CLIENTS:
                    clients.append(words)
            if not clients:
                continue
            body = str(entry["body"])
            if not entry["quoted"] and has_shell_expansion(body):
                return "sql-stdin"
            reason = detect_sql(body)
            if reason:
                return reason

    for group in groups:
        for receiver_index in range(1, len(group)):
            receiver = shell_words(group[receiver_index])
            receiver = unwrap_command(receiver)
            if receiver and os.path.basename(receiver[0]).lower() in SQL_CLIENTS:
                producer = shell_words(group[receiver_index - 1])
                producer = unwrap_command(producer)
                source_is_heredoc = any(
                    group in split_shell_groups(str(entry["header"]))
                    for entry in entries
                )
                if producer:
                    name = os.path.basename(producer[0]).lower()
                    if name in ("echo", "printf"):
                        producer_segment = group[receiver_index - 1]
                        if has_shell_expansion(producer_segment):
                            return "sql-stdin"
                        if name == "echo":
                            if "-e" in producer[1:] and "\\" in producer_segment:
                                return "sql-stdin"
                            sql_text = " ".join(w for w in producer[1:] if w not in ("-n", "-e", "-E"))
                        else:
                            sql_text = printf_sql_text(producer)
                            if sql_text is None:
                                return "sql-stdin"
                        reason = detect_sql(sql_text)
                        if reason:
                            return reason
                    elif not source_is_heredoc:
                        return "sql-stdin"

        for segment in group:
            words = unwrap_command(shell_words(segment))
            if words and os.path.basename(words[0]).lower() in SQL_CLIENTS and has_stdin_redirection(segment):
                if "<<" not in segment or not any(
                    group in split_shell_groups(str(entry["header"])) for entry in entries
                ):
                    return "sql-stdin"
    return None


def inspect_shell_heredocs(script: str, depth: int) -> str | None:
    """Inspect here-documents that a recognized shell executes from stdin."""
    for entry in heredoc_entries(script):
        for group in split_shell_groups(str(entry["header"])):
            for segment in group:
                words = unwrap_command(shell_words(segment))
                if (
                    words
                    and os.path.basename(words[0]).lower() in SHELLS
                    and shell_reads_stdin_as_script(words)
                ):
                    reason = inspect_command(str(entry["body"]), depth + 1)
                    if reason:
                        return reason
    return None


def inspect_shell_stdin(script: str, entries: list[dict[str, object]], depth: int) -> str | None:
    """Reject opaque shell scripts delivered over stdin; inspect simple literal producers."""
    known_headers = [group for entry in entries for group in split_shell_groups(str(entry["header"]))]
    for group in split_shell_groups(script):
        known_heredoc = any(group == header for header in known_headers)
        for index, segment in enumerate(group):
            words = unwrap_command(shell_words(segment))
            if not words or os.path.basename(words[0]).lower() not in SHELLS:
                continue
            # A -c script is already inspected by classify_segment, not read from stdin.
            command_option = False
            for word in words[1:]:
                # After --, values such as -c are positional arguments, not options.
                if word == "--" or not word.startswith("-"):
                    break
                if word == "-c" or (not word.startswith("--") and "c" in word[1:]):
                    command_option = True
                    break
            if command_option:
                continue
            if has_stdin_redirection(segment, allow_heredoc=known_heredoc):
                return "analysis"
            if index == 0 or known_heredoc or not shell_reads_stdin_as_script(words):
                continue
            producer_segment = group[index - 1]
            producer = unwrap_command(shell_words(producer_segment))
            if not producer or has_shell_expansion(producer_segment):
                return "analysis"
            name = os.path.basename(producer[0]).lower()
            if name == "echo":
                echo_options = []
                for word in producer[1:]:
                    if len(word) > 1 and word.startswith("-") and set(word[1:]) <= set("neE"):
                        echo_options.append(word)
                    else:
                        break
                if any("e" in word for word in echo_options) and "\\" in producer_segment:
                    return "analysis"
                body = " ".join(producer[1 + len(echo_options):])
            elif name == "printf":
                body = printf_sql_text(producer)
            else:
                return "analysis"
            if body is None or has_shell_expansion(body):
                return "analysis"
            reason = inspect_command(body, depth + 1)
            if reason:
                return reason
    return None


def classify_segment(segment: str, depth: int = 0) -> str | None:
    words = shell_words(segment)
    words = unwrap_command(words)
    if not words:
        return None
    reason = detect_rm(words) or detect_git_force_push(words)
    if reason:
        return reason
    head = os.path.basename(words[0]).lower()
    if head in SHELLS or head == "eval":
        for i, word in enumerate(words[1:], start=1):
            if head == "eval":
                return inspect_command(" ".join(words[1:]), depth + 1) if len(words) > 1 else None
            if word == "-c" or (word.startswith("-") and "c" in word[1:] and not word.startswith("--")):
                if i + 1 < len(words):
                    return inspect_command(words[i + 1], depth + 1)
    for statement in extract_sql(words):
        reason = detect_sql(statement)
        if reason:
            return reason
    return None


def inspect_command(script: str, depth: int = 0) -> str | None:
    if depth > 8:
        raise ValueError("command nesting limit")
    entries = heredoc_entries(script)
    shell_script = mask_heredoc_bodies(script, entries)
    nested_commands = extract_substitutions(shell_script)
    for entry in entries:
        if not entry["quoted"]:
            nested_commands.extend(extract_substitutions(str(entry["body"])))
    for nested in nested_commands:
        reason = inspect_command(nested, depth + 1)
        if reason:
            return reason
    reason = inspect_shell_heredocs(script, depth)
    if reason:
        return reason
    reason = inspect_sql_pipelines(script)
    if reason:
        return reason
    reason = inspect_shell_stdin(shell_script, entries, depth)
    if reason:
        return reason
    for segment in split_shell_commands(shell_script):
        reason = classify_segment(segment, depth)
        if reason:
            return reason
    return None


_SECRET_VALUE = r'("(?:[^"\\]|\\.)*"|\'[^\']*\'|[^\s;&|]+)'
_SECRET_NAME = r"(?:[A-Za-z_][A-Za-z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASSWD|API[_-]?KEY|ACCESS[_-]?KEY|CLIENT[_-]?SECRET|AUTHORIZATION|CREDENTIALS?)[A-Za-z0-9_]*|PASSWORD|PASSWD|TOKEN|SECRET|API[_-]?KEY|ACCESS[_-]?KEY|CLIENT[_-]?SECRET|AUTHORIZATION|CREDENTIALS?)"
_SECRET_ASSIGNMENT = re.compile(
    rf"(?i)(\b{_SECRET_NAME}\b\s*(?:=|:)\s*){_SECRET_VALUE}"
)
_SECRET_FLAG = re.compile(
    rf"(?i)(--(?:password|passwd|token|secret|api-key|access-key|client-secret)(?:=|\s+)){_SECRET_VALUE}"
)
_BEARER = re.compile(r"(?i)(\bbearer\s+)[A-Za-z0-9._~+/=-]+")
_URL_CREDENTIAL = re.compile(r"(?i)((?:https?|ftp)://[^/\s:@]+:)[^/\s@]+(@)")


def redact_command(command: str) -> str:
    redacted = _SECRET_ASSIGNMENT.sub(r"\1[REDACTED]", command)
    redacted = _SECRET_FLAG.sub(r"\1[REDACTED]", redacted)
    redacted = _BEARER.sub(r"\1[REDACTED]", redacted)
    redacted = _URL_CREDENTIAL.sub(r"\1[REDACTED]\2", redacted)
    redacted = "".join(ch if ch >= " " and ch != "\x7f" else " " for ch in redacted)
    if len(redacted) > MAX_LOG_COMMAND_CHARS:
        redacted = redacted[:MAX_LOG_COMMAND_CHARS] + "…[truncated]"
    return redacted


def safe_project_path(value: object) -> str:
    if not isinstance(value, str) or not value:
        return "unknown"
    value = "".join(ch if ch >= " " and ch != "\x7f" else " " for ch in value)
    return value[:MAX_PROJECT_CHARS]


def write_log(home: Path, command: str, project: str, reason: str) -> bool:
    """Append a bounded JSONL record; never follow a log symlink."""
    try:
        claude_dir = home / ".claude"
        hooks_dir = claude_dir / "hooks"
        for directory in (claude_dir, hooks_dir):
            try:
                # Validate each parent before creating its child. In
                # particular, do not create ~/.claude/hooks through a symlink.
                if directory == hooks_dir:
                    parent_info = claude_dir.lstat()
                    if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(parent_info.st_mode):
                        return False
                directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
            info = directory.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                return False
        path = hooks_dir / "blocked.log"
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "command": redact_command(command),
            "project_path": safe_project_path(project),
            "reason": reason,
        }
        line = (json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(path, flags, 0o600)
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink > 1:
                return False
            os.fchmod(fd, 0o600)
            if info.st_size + len(line) > MAX_LOG_BYTES:
                # Keep the latest block while bounding retention. This log is
                # local diagnostic context, not a complete audit archive.
                os.ftruncate(fd, 0)
                record["previous_log_truncated"] = True
                line = (json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n").encode("utf-8")
            view = memoryview(line)
            while view:
                written = os.write(fd, view)
                view = view[written:]
        finally:
            os.close(fd)
        return True
    except (OSError, ValueError, TypeError):
        return False


def emit_block(reason: str) -> int:
    print(BLOCKED_MESSAGES.get(reason, BLOCKED_MESSAGES["analysis"]), file=sys.stderr)
    return 2


def run(payload: bytes, home: Path | None = None) -> tuple[int, str]:
    """Return (exit_code, block_reason); empty reason means normal permission flow."""
    home = home or Path.home()

    def block_input(command: str, project: object) -> tuple[int, str]:
        logged = write_log(home, command, safe_project_path(project), "input")
        return 2, "input" if logged else "log-failed:input"

    if len(payload) > MAX_INPUT_BYTES:
        return block_input("<omitted: hook input exceeded size limit>", "unknown")
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, ValueError):
        return block_input("<omitted: invalid hook input>", "unknown")
    if not isinstance(data, dict):
        return block_input("<omitted: invalid hook input>", "unknown")
    if not isinstance(data.get("tool_name"), str):
        return block_input("<omitted: missing or invalid tool name>", data.get("cwd", "unknown"))
    if data.get("tool_name") != "Bash":
        return 0, ""
    tool_input = data.get("tool_input")
    if not isinstance(tool_input, dict) or not isinstance(tool_input.get("command"), str):
        return block_input("<omitted: missing Bash command>", data.get("cwd", "unknown"))
    command = tool_input["command"]
    project = safe_project_path(data.get("cwd", "unknown"))
    if "\x00" in command or len(command) > MAX_COMMAND_CHARS:
        return block_input(command, project)
    try:
        reason = inspect_command(command)
    except (ValueError, RecursionError):
        reason = "analysis"
    if not reason:
        return 0, ""
    logged = write_log(home, command, project, reason)
    return 2, reason if logged else f"log-failed:{reason}"


def main() -> int:
    payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    code, reason = run(payload)
    if code == 0:
        return 0  # Empty stdout/stderr: leave the normal permission flow intact.
    if reason.startswith("log-failed:"):
        underlying = reason.partition(":")[2]
        print(
            f"{BLOCKED_MESSAGES.get(underlying, BLOCKED_MESSAGES['analysis'])} "
            "The command remains blocked, but ~/.claude/hooks/blocked.log could not be written. Check log permissions or symlinks.",
            file=sys.stderr,
        )
        return 2
    return emit_block(reason)


if __name__ == "__main__":
    raise SystemExit(main())
