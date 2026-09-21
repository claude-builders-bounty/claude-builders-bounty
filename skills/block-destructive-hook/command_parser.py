#!/usr/bin/env python3
"""Small shell-command tokenizer and destructive-intent classifier.

This is intentionally not a shell parser or executor. It only recognizes command
words, separators, options, and quoted arguments well enough for the hook's
contract; quoted documentation/echo text is never treated as a command.
"""
from __future__ import annotations

import os
import posixpath
import re
import sys
from dataclasses import dataclass


@dataclass
class Token:
    value: str
    quoted: bool = False


# Bash's ANSI-C quoting ($'...') decodes backslash escapes into literal bytes
# before the word is used as a command or argument. Recognizing this table
# structurally (rather than pattern-matching specific payloads) keeps escaped
# targets like $'/' or $'\x2f' from bypassing the token-level checks below.
_ANSI_C_ESCAPES = {
    "a": "\a", "b": "\b", "e": "\x1b", "E": "\x1b", "f": "\f",
    "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\",
    "'": "'", '"': '"', "?": "?",
}


def _decode_ansi_c(body: str) -> str:
    """Decode the escapes bash recognizes inside a $'...' word."""
    out: list[str] = []

    def safe_chr(value: int) -> str:
        try:
            return chr(value)
        except (OverflowError, ValueError):
            # Invalid Unicode escapes must not crash the safety parser and
            # accidentally turn a destructive command into a fail-open result.
            return "\ufffd"

    i = 0
    while i < len(body):
        ch = body[i]
        if ch != "\\" or i + 1 >= len(body):
            out.append(ch)
            i += 1
            continue
        nxt = body[i + 1]
        if nxt in _ANSI_C_ESCAPES:
            out.append(_ANSI_C_ESCAPES[nxt])
            i += 2
        elif nxt == "x":
            m = re.match(r"[0-9A-Fa-f]{1,2}", body[i + 2 :])
            if m:
                out.append(safe_chr(int(m.group(), 16)))
                i += 2 + len(m.group())
            else:
                out.append(ch)
                i += 1
        elif nxt in "01234567":
            m = re.match(r"[0-7]{1,3}", body[i + 1 :])
            out.append(safe_chr(int(m.group(), 8) & 0xFF))
            i += 1 + len(m.group())
        elif nxt in "uU":
            width = 4 if nxt == "u" else 8
            m = re.match(r"[0-9A-Fa-f]{1,%d}" % width, body[i + 2 :])
            if m:
                out.append(safe_chr(int(m.group(), 16)))
                i += 2 + len(m.group())
            else:
                out.append(ch)
                i += 1
        elif nxt == "c" and i + 2 < len(body):
            out.append(safe_chr(ord(body[i + 2].upper()) ^ 0x40))
            i += 3
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def _split_top_level(body: str, sep: str) -> list[str]:
    """Split on sep, ignoring occurrences nested inside braces."""
    parts: list[str] = []
    depth = 0
    buf: list[str] = []
    for ch in body:
        if ch == "{":
            depth += 1
            buf.append(ch)
        elif ch == "}":
            depth -= 1
            buf.append(ch)
        elif ch == sep and depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


_MAX_BRACE_ITEMS = 5000


def _expand_brace_range(body: str) -> list[str] | None:
    m = re.fullmatch(r"(-?\d+)\.\.(-?\d+)(?:\.\.(-?\d+))?", body)
    if m:
        start_s, end_s, step_s = m.groups()
        start, end = int(start_s), int(end_s)
        step = abs(int(step_s)) if step_s else 1
        step = step or 1
        step = step if start <= end else -step
        width = 0
        if (start_s.startswith("0") and len(start_s) > 1) or (end_s.startswith("0") and len(end_s) > 1):
            width = max(len(start_s.lstrip("-")), len(end_s.lstrip("-")))
        values = range(start, end + (1 if step > 0 else -1), step)
        if len(values) > _MAX_BRACE_ITEMS:
            return None
        if width:
            return [f"{v:0{width}d}" if v >= 0 else f"-{abs(v):0{max(width - 1, 1)}d}" for v in values]
        return [str(v) for v in values]
    m = re.fullmatch(r"([A-Za-z])\.\.([A-Za-z])(?:\.\.(-?\d+))?", body)
    if m:
        start_c, end_c, step_s = m.groups()
        start, end = ord(start_c), ord(end_c)
        step = abs(int(step_s)) if step_s else 1
        step = step or 1
        step = step if start <= end else -step
        values = range(start, end + (1 if step > 0 else -1), step)
        return [chr(v) for v in values]
    return None


class _BraceExpansionLimitExceeded(Exception):
    pass


def expand_braces(word: str) -> list[str]:
    """Expand bash brace expressions such as {a,b,c} and {1..5} in a word.

    Only unquoted words reach this (callers skip quoted tokens), matching
    bash's own rule that brace expansion never applies inside quotes.
    """
    try:
        return _expand_braces(word, [0])
    except _BraceExpansionLimitExceeded:
        # Chained/nested groups (e.g. "{a,b}" repeated 20 times) expand
        # combinatorially; bail out rather than let one adversarial token
        # hang the classifier, and fall back to the literal, unexpanded word.
        return [word]


def _expand_braces(word: str, counter: list[int]) -> list[str]:
    start = word.find("{")
    if start == -1:
        return [word]
    depth = 0
    end = -1
    i = start
    while i < len(word):
        if word[i] == "{":
            depth += 1
        elif word[i] == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
        i += 1
    if end == -1:
        return [word]
    prefix, body, suffix = word[:start], word[start + 1 : end], word[end + 1 :]
    parts = _split_top_level(body, ",")
    if len(parts) > 1:
        items = parts
    else:
        items = _expand_brace_range(body)
        if items is None:
            # No top-level comma or valid range: this pair is not a brace
            # expansion and stays literal, matching bash's own rule.
            return [word]
    results: list[str] = []
    for item in items:
        for candidate in _expand_braces(prefix + item + suffix, counter):
            counter[0] += 1
            if counter[0] > _MAX_BRACE_ITEMS:
                raise _BraceExpansionLimitExceeded()
            results.append(candidate)
    return results


# Utility wrappers that execute a trailing command still accept their own
# flags first. Some flags take a value that may be fused (-n19), given with
# "=" (--adjustment=19), or passed as a separate argument (-n 19); only the
# last form should consume an extra token, or the wrapper's real payload
# (e.g. the "rm" in "nice -n19 rm -rf /") is swallowed as a flag value.
WRAPPER_VALUE_OPTIONS: dict[str, set[str]] = {
    # GNU/BSD time options which consume the following argv word. Without
    # these, `time -o file rm ...` mistakes `file` for the payload command.
    "time": {"-o", "--output", "-f", "--format"},
    "nice": {"-n", "--adjustment"},
    "timeout": {"-k", "--kill-after", "-s", "--signal"},
    "nohup": set(),
    "exec": {"-a"},
    "xargs": {"-a", "--arg-file", "-d", "--delimiter", "-E", "-I", "--replace",
              "-L", "--max-lines", "-n", "--max-args", "-P", "--max-procs",
              "-s", "--max-chars"},
}

# SQL clients accept the statement/command either as a separate argument, a
# "--opt=value" long form, or fused directly onto a short flag (-cVALUE).
SQL_SHORT_VALUE_OPTIONS = {"-c", "-e", "-Q", "-q"}
SQL_LONG_VALUE_OPTIONS = {"--command", "--execute"}
SQL_EXACT_VALUE_OPTIONS = SQL_SHORT_VALUE_OPTIONS | SQL_LONG_VALUE_OPTIONS | {"-cmd"}


def sql_client_statements(tokens: list[Token], index: int) -> list[str]:
    """Return every candidate SQL statement passed to a SQL client invocation."""
    args = tokens[index + 1 :]
    client = posixpath.basename(tokens[index].value).lower()
    statements: list[str] = []
    # sqlite3 takes a database filename first, then an optional SQL argument;
    # the other supported clients require an explicit execution option for
    # argv SQL. Do not mistake a database filename for executable SQL.
    if client == "sqlite3":
        # Skip sqlite options before locating the database positional. -cmd
        # and -init execute SQL themselves; other value-taking options merely
        # configure the client and must not be mistaken for SQL.
        sqlite_value_options = {"-cmd", "-init", "-separator", "-nullvalue",
                                "-newline", "-lookaside"}
        positional: list[str] = []
        i = 0
        while i < len(args):
            value = args[i].value
            if value == "--":
                positional.extend(item.value for item in args[i + 1 :])
                break
            if value == "-cmd" and i + 1 < len(args):
                statements.append(args[i + 1].value)
                i += 2
            elif value in sqlite_value_options and i + 1 < len(args):
                i += 2
            elif value.startswith("-"):
                i += 1
            else:
                positional.append(value)
                i += 1
        statements.extend(item for item in positional[1:] if not item.startswith("."))
    for position, token in enumerate(args):
        value = token.value
        if value in SQL_EXACT_VALUE_OPTIONS and position + 1 < len(args):
            statements.append(" ".join(item.value for item in args[position + 1 :]))
            continue
        for option in SQL_LONG_VALUE_OPTIONS:
            if value.startswith(option + "="):
                statements.append(value[len(option) + 1 :])
        for option in SQL_SHORT_VALUE_OPTIONS:
            if value.startswith(option) and value != option:
                statements.append(value[len(option) :])
    return statements


_SHELL_WORDS = {"sh", "bash", "zsh", "dash", "ksh", "shell"}
_SCRIPT_SOURCE_WORDS = _SHELL_WORDS | {"source"}


def _read_shell_word(text: str, pos: int) -> tuple[str | None, int]:
    """Read one shell word (quoted or bare) starting at pos."""
    n = len(text)
    if pos >= n:
        return None, pos
    if text.startswith("$'", pos):
        j = pos + 2
        while j < n and text[j] != "'":
            j += 2 if text[j] == "\\" and j + 1 < n else 1
        return _decode_ansi_c(text[pos + 2 : j]), min(j + 1, n)
    if text[pos] in "'\"":
        q = text[pos]
        j = pos + 1
        while j < n and text[j] != q:
            j += 2 if text[j] == "\\" and j + 1 < n else 1
        return text[pos + 1 : j], min(j + 1, n)
    j = pos
    while j < n and text[j] not in " \t\r\n;|&":
        j += 1
    return (text[pos:j] if j > pos else None), j


def here_document_payloads(text: str) -> list[str]:
    """Return payloads fed to a shell via ``<<<`` here-strings or ``<<`` heredocs.

    Both redirections feed text to the *preceding* command's stdin; when that
    command is a shell invoked without ``-c``, it reads and executes that
    text as a script, exactly like ``printf ... | sh``. The scan tracks quote
    state itself (rather than using a regex over the raw text) so a `<<<`
    that only appears inside quoted documentation, e.g. ``echo "sh <<< x"``,
    is never mistaken for a real redirection.
    """
    payloads: list[str] = []
    i = 0
    n = len(text)
    quote: str | None = None
    ansi_quote = False
    word_start = 0
    last_word = ""

    def flush_word(end: int) -> None:
        nonlocal last_word, word_start
        if end > word_start:
            last_word = text[word_start:end]
        word_start = end

    while i < n:
        ch = text[i]
        if quote == "'":
            if ansi_quote and ch == "\\":
                i += 2
                continue
            if ch == "'":
                quote = None
                ansi_quote = False
            i += 1
            continue
        if quote == '"':
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                quote = None
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if ch in "'\"":
            ansi_quote = ch == "'" and i > 0 and text[i - 1] == "$"
            quote = ch
            i += 1
            continue
        if ch in " \t\r\n;|&()":
            flush_word(i)
            word_start = i + 1
            i += 1
            continue
        if text.startswith("<<<", i):
            flush_word(i)
            boundary = max(text.rfind(c, 0, i) for c in ";\n|&")
            commands = tokenize(text[boundary + 1 : i])
            word = command_name(commands[-1])[0] if commands else None
            j = i + 3
            while j < n and text[j] in " \t":
                j += 1
            payload_word, j = _read_shell_word(text, j)
            if word in _SHELL_WORDS and payload_word is not None:
                payloads.append(payload_word)
            i = word_start = j
            continue
        if text.startswith("<<", i):
            flush_word(i)
            word = posixpath.basename(last_word)
            j = i + 2
            if j < n and text[j] == "-":
                j += 1
            while j < n and text[j] in " \t":
                j += 1
            quote_char = ""
            if j < n and text[j] in "'\"":
                quote_char = text[j]
                j += 1
            delim_start = j
            while j < n and (text[j].isalnum() or text[j] == "_"):
                j += 1
            delim = text[delim_start:j]
            if quote_char and j < n and text[j] == quote_char:
                j += 1
            while j < n and text[j] != "\n":
                j += 1
            j += 1
            body_start = j
            if delim:
                m = re.compile(r"^[ \t]*" + re.escape(delim) + r"[ \t]*$", re.M).search(text, body_start)
                if m:
                    if word in _SHELL_WORDS:
                        payloads.append(text[body_start : m.start()])
                    j = m.end()
            i = word_start = j
            continue
        i += 1
    return payloads


def _read_heredoc_delimiter(text: str, start: int) -> tuple[str, int, bool]:
    """Read a shell heredoc word, including adjacent quoted word pieces."""
    i = start
    value: list[str] = []
    quoted = False
    while i < len(text) and text[i] not in " \t\r\n;|&<>":
        if text.startswith("$'", i):
            quoted = True
            j = i + 2
            while j < len(text) and text[j] != "'":
                j += 2 if text[j] == "\\" and j + 1 < len(text) else 1
            value.append(_decode_ansi_c(text[i + 2 : j]))
            i = min(j + 1, len(text))
        elif text[i] == "\\" and i + 1 < len(text):
            quoted = True
            value.append(text[i + 1])
            i += 2
        elif text[i] in "'\"":
            quoted = True
            q = text[i]
            i += 1
            while i < len(text) and text[i] != q and text[i] not in "\r\n":
                if text[i] == "\\" and i + 1 < len(text):
                    value.append(text[i + 1])
                    i += 2
                else:
                    value.append(text[i])
                    i += 1
            if i < len(text) and text[i] == q:
                i += 1
        else:
            value.append(text[i])
            i += 1
    return "".join(value), i, quoted


def split_heredocs(text: str) -> tuple[str, list[str], list[str]]:
    """Mask heredoc bodies and return executable shell/expansion payloads.

    Plain heredoc text is data, not a command (``cat <<EOF`` must not classify
    a line containing ``rm -rf``). An unquoted delimiter still permits shell
    substitutions, while a shell consumer executes its body as a script.
    """
    masked = list(text)
    shell_payloads: list[str] = []
    expansion_payloads: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\" and quote == '"':
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if not text.startswith("<<", i) or text.startswith("<<<", i):
            i += 1
            continue

        op = i
        j = i + 2
        strip_tabs = j < len(text) and text[j] == "-"
        if strip_tabs:
            j += 1
        while j < len(text) and text[j] in " \t":
            j += 1
        delim, j, quoted = _read_heredoc_delimiter(text, j)
        line_end = text.find("\n", j)
        if not delim or line_end < 0:
            i = j
            continue
        body_start = line_end + 1
        # Accept a terminator followed by a command separator as a defensive
        # recovery for pasted/malformed shell input, while leaving the
        # separator itself visible to the ordinary command tokenizer.
        pattern = (
            r"^"
            + (r"\t*" if strip_tabs else "")
            + re.escape(delim)
            + r"[ \t]*(?=;|\r?$)"
        )
        match = re.compile(pattern, re.M).search(text, body_start)
        if not match:
            i = j
            continue
        body = text[body_start : match.start()]

        # Resolve the command segment immediately preceding the redirection.
        boundary = max(text.rfind(c, 0, op) for c in ";\n|&")
        prefix_commands = tokenize(text[boundary + 1 : op])
        consumer = command_name(prefix_commands[-1])[0] if prefix_commands else None
        if consumer in _SHELL_WORDS:
            shell_payloads.append(body)
        elif not quoted:
            expansion_payloads.append(body)

        # Preserve newlines so command boundaries remain intact, but hide data
        # and the terminator from the ordinary command tokenizer.
        for k in range(body_start, match.end()):
            if masked[k] != "\n":
                masked[k] = " "
        i = match.end()
    return "".join(masked), shell_payloads, expansion_payloads


def _word_scan(text: str, on_char) -> None:
    """Shared quote-aware scan used by the redirection/substitution
    detectors below: tracks quote state (including $'...' escapes) and the
    most recently completed top-level word, and calls ``on_char`` at every
    unquoted, top-level character *before* applying default word-boundary
    handling, so a caller's own multi-character syntax (``<(``, a lone
    ``|``) gets first refusal instead of being silently consumed by the
    generic boundary handling below.
    """
    i = 0
    n = len(text)
    quote: str | None = None
    ansi_quote = False
    word_start = 0
    last_word = ""

    def flush_word(end: int) -> None:
        nonlocal last_word, word_start
        if end > word_start:
            last_word = text[word_start:end]
        word_start = end

    while i < n:
        ch = text[i]
        if quote == "'":
            if ansi_quote and ch == "\\":
                i += 2
                continue
            if ch == "'":
                quote = None
                ansi_quote = False
            i += 1
            continue
        if quote == '"':
            if ch == "\\":
                i += 2
                continue
            if ch == '"':
                quote = None
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if ch in "'\"":
            ansi_quote = ch == "'" and i > 0 and text[i - 1] == "$"
            quote = ch
            i += 1
            continue
        step = on_char(text, i, last_word, flush_word)
        if step is not None:
            i = word_start = step
            continue
        if ch in " \t\r\n;|&()":
            flush_word(i)
            word_start = i + 1
            i += 1
            continue
        i += 1


def shell_process_substitution_targets(text: str) -> bool:
    """True if a shell/interpreter is given a ``<(...)`` process substitution
    as an argument. Bash runs such a substitution to produce a real file
    (typically /dev/fd/N); when the consuming command reads its argument as
    script source -- exactly what ``sh``/``bash``/... do with a positional
    filename, or what ``source`` does with any filename -- that generated
    content is executed just as if it had been piped in directly.
    """
    found = False

    def on_word(text: str, i: int, last_word: str, flush_word) -> int | None:
        nonlocal found
        if text.startswith("<(", i):
            flush_word(i)
            boundary = max(text.rfind(c, 0, i) for c in ";\n|&")
            commands = tokenize(text[boundary + 1 : i])
            consumer = command_name(commands[-1])[0] if commands else None
            if consumer in _SCRIPT_SOURCE_WORDS:
                found = True
            return i + 2
        return None

    _word_scan(text, on_word)
    return found


def pipe_shell_targets(text: str) -> list[str]:
    """Return the raw text of each command segment immediately following a
    real pipe (a single unquoted ``|``, not ``||``). A pipe feeds the
    previous command's output to this segment's stdin; when this segment
    resolves (through wrappers) to a shell reading no script/-c argument,
    that stdin is executed as code.
    """
    segments: list[str] = []

    def on_word(text: str, i: int, last_word: str, flush_word) -> int | None:
        if text[i] == "|" and (i + 1 >= len(text) or text[i + 1] != "|") and (i == 0 or text[i - 1] != "|"):
            flush_word(i)
            j = i + 1
            while j < len(text) and text[j] in " \t":
                j += 1
            k = j
            while k < len(text) and text[k] not in ";\n|&":
                k += 1
            segments.append(text[j:k])
            return j
        return None

    _word_scan(text, on_word)
    return segments


def tokenize(text: str) -> list[list[Token]]:
    """Tokenize simple shell command lists, preserving command boundaries."""
    commands: list[list[Token]] = [[]]
    buf: list[str] = []
    had_quote = False
    quote: str | None = None
    escaped = False
    i = 0

    def flush() -> None:
        nonlocal buf, had_quote
        if buf or had_quote:
            commands[-1].append(Token("".join(buf), had_quote))
            buf, had_quote = [], False

    while i < len(text):
        ch = text[i]
        if escaped:
            buf.append(ch)
            escaped = False
        elif quote:
            if ch == "\\" and quote == '"' and i + 1 < len(text):
                buf.append(text[i + 1])
                i += 1
            elif ch == quote:
                quote = None
                had_quote = True
            else:
                buf.append(ch)
        elif ch == "$" and i + 1 < len(text) and text[i + 1] == "'":
            j = i + 2
            while j < len(text) and text[j] != "'":
                if text[j] == "\\" and j + 1 < len(text):
                    j += 2
                else:
                    j += 1
            buf.append(_decode_ansi_c(text[i + 2 : j]))
            had_quote = True
            i = j
        elif ch in "'\"":
            quote = ch
            had_quote = True
        elif ch == "\\":
            escaped = True
        elif ch == "#" and (not buf and (not commands[-1] or True)):
            # At a token boundary, # starts a shell comment. A # in a word is data.
            while i < len(text) and text[i] != "\n":
                i += 1
            continue
        elif ch in " \t\r":
            flush()
        elif ch == "\n" or ch == ";":
            flush()
            if commands[-1]:
                commands.append([])
        elif ch in "|&()":
            flush()
            if i + 1 < len(text) and text[i + 1] == ch:
                i += 1
            if commands[-1]:
                commands.append([])
        else:
            buf.append(ch)
        i += 1
    if escaped:
        buf.append("\\")
    flush()
    expanded: list[list[Token]] = []
    for command in commands:
        if not command:
            continue
        new_command: list[Token] = []
        for token in command:
            if token.quoted:
                new_command.append(token)
            else:
                new_command.extend(Token(piece) for piece in expand_braces(token.value))
        expanded.append(new_command)
    return expanded


def shell_substitutions(text: str) -> list[str]:
    """Return commands executed by shell substitution constructs.

    This intentionally understands only the quoting needed to distinguish shell
    syntax from literal documentation.  In particular, substitutions in single
    quotes (and escaped substitutions) are data, while substitutions in double
    quotes still execute. Process substitutions ``<(...)`` and ``>(...)`` are
    included because Bash evaluates their bodies before the surrounding command.
    """
    found: list[str] = []
    i = 0
    quote: str | None = None
    ansi_quote = False
    while i < len(text):
        ch = text[i]
        if quote == "'":
            if ansi_quote and ch == "\\":
                i += 2
                continue
            if ch == "'":
                quote = None
                ansi_quote = False
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if quote == '"':
            if ch == '"':
                quote = None
                i += 1
                continue
            if text.startswith(("$(", "<(", ">("), i):
                body, end = _parenthesized_substitution(text, i + 2)
                if body is not None:
                    found.append(body)
                    i = end
                    continue
            elif ch == "`":
                body, end = _backtick_substitution(text, i + 1)
                if body is not None:
                    found.append(body)
                    i = end
                    continue
            i += 1
            continue
        if ch in "'\"":
            ansi_quote = ch == "'" and i > 0 and text[i - 1] == "$"
            quote = ch
            i += 1
        elif ch == "\\":
            i += 2
        elif text.startswith(("$(", "<(", ">("), i):
            body, end = _parenthesized_substitution(text, i + 2)
            if body is not None:
                found.append(body)
                i = end
            else:
                i += 2
        elif ch == "`":
            body, end = _backtick_substitution(text, i + 1)
            if body is not None:
                found.append(body)
                i = end
            else:
                i += 1
        else:
            i += 1
    return found


def _backtick_substitution(text: str, start: int) -> tuple[str | None, int]:
    i = start
    while i < len(text):
        if text[i] == "\\":
            i += 2
        elif text[i] == "`":
            return text[start:i], i + 1
        else:
            i += 1
    return None, start


def _parenthesized_substitution(text: str, start: int) -> tuple[str | None, int]:
    depth = 1
    i = start
    quote: str | None = None
    while i < len(text):
        ch = text[i]
        if quote == "'":
            if ch == "'":
                quote = None
            i += 1
            continue
        if ch == "\\":
            i += 2
            continue
        if quote == '"':
            if ch == '"':
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
        elif text.startswith(("$(", "<(", ">("), i):
            # Nested substitutions of any of the three forms open a new
            # level; only counting "$(" here would let a nested <( or >(
            # supply an extra ")" that closes this substitution too early,
            # truncating (and hiding) the rest of its body.
            depth += 1
            i += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[start:i], i + 1
        i += 1
    return None, start


_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

_SHELL_RESERVED = {
    "if", "then", "else", "elif", "fi", "for", "while", "until", "do",
    "done", "case", "esac", "in", "function", "{", "}",
}

_PREFIX_VALUE_OPTIONS: dict[str, set[str]] = {
    "sudo": {"-u", "--user", "-g", "--group", "-h", "--host", "-p",
             "--prompt", "-C", "--chdir", "-D", "-R", "--chroot", "-T",
             "--close-from", "-r", "--role", "-t", "--type"},
    "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
    "command": set(),
    "builtin": set(),
}


def _skip_utility_options(tokens: list[Token], index: int, value_options: set[str]) -> int:
    """Skip one utility's options without consuming its payload command."""
    while index < len(tokens):
        value = tokens[index].value
        if value == "--":
            return index + 1
        if not value.startswith("-") or value == "-":
            return index
        if value.startswith("--"):
            name, attached = value.split("=", 1)[0], "=" in value
        else:
            name, attached = value[:2], len(value) > 2
        index += 1
        if name in value_options and not attached:
            index += 1
    return index


def command_name(tokens: list[Token]) -> tuple[str | None, int]:
    """Return executable name and index after command-prefix wrappers.

    Prefixes are matched on basename and their options are consumed according
    to whether those options take values. This covers absolute paths and avoids
    both swallowing a payload and mistaking an option value for an executable.
    """
    i = 0
    while i < len(tokens):
        word = tokens[i].value
        base = posixpath.basename(word)
        if base in _SHELL_RESERVED:
            i += 1
            continue
        if base == "!":
            i += 1
            continue
        if _ASSIGNMENT_RE.match(word):
            i += 1
            continue
        if base in _PREFIX_VALUE_OPTIONS:
            i = _skip_utility_options(tokens, i + 1, _PREFIX_VALUE_OPTIONS[base])
            if base == "env":
                while i < len(tokens) and _ASSIGNMENT_RE.match(tokens[i].value):
                    i += 1
            continue
        if base in WRAPPER_VALUE_OPTIONS:
            i = _skip_utility_options(tokens, i + 1, WRAPPER_VALUE_OPTIONS[base])
            if base == "timeout":
                while i < len(tokens) and re.fullmatch(
                    r"[0-9]+(?:\.[0-9]+)?(?:ms|s|m|h|d)?", tokens[i].value
                ):
                    i += 1
            if base == "xargs" and i >= len(tokens):
                return "echo", i
            continue
        return base, i
    return None, i


def shell_rm_dangerous(tokens: list[Token], index: int) -> bool:
    args = tokens[index + 1 :]
    options_done = False
    recursive = force = False
    targets: list[str] = []
    for token in args:
        word = token.value
        if not options_done and word == "--":
            options_done = True
        elif not options_done and word.startswith("-") and word != "-":
            if word.startswith("--"):
                recursive |= word == "--recursive"
                force |= word == "--force"
            else:
                flags = word[1:]
                recursive |= "r" in flags or "R" in flags
                force |= "f" in flags
            continue
        else:
            options_done = True
            targets.append(word)

    # The acceptance contract says to block the rm -rf pattern, regardless of
    # target. This also closes glob/expansion bypasses which cannot be resolved
    # safely without executing the user's shell.
    if recursive and force and targets:
        return True

    # Preserve protection for especially dangerous rm targets even when one of
    # -r/-f is omitted.
    for target in targets:
        expanded = target
        if expanded == "~" or expanded.startswith("~/"):
            expanded = os.path.expanduser(expanded)
        if expanded == "$HOME" or expanded.startswith("$HOME/"):
            expanded = os.path.expanduser("~") + expanded[5:]
        normalized = posixpath.normpath(expanded)
        if normalized in {"/", ".", ".."} or normalized.startswith("../"):
            return True
        if expanded == "./build" or expanded.startswith("./build/"):
            return True
        if expanded in {"*", "./*", ".?*"} or expanded.startswith("/*"):
            return True
        if normalized.startswith(("/var", "/etc", "/usr", "/bin", "/sbin", "/home", "/Users", "/System", "/Library")):
            return True
    return False


def sql_code(value: str, preserve_identifiers: bool = False, dialect: str | None = None) -> str:
    """Mask SQL comments and quoted literals while preserving code layout."""
    out = list(value)
    i = 0
    state: str | None = None
    dollar_tag: str | None = None
    while i < len(value):
        if dollar_tag is not None:
            end = value.find(dollar_tag, i)
            if end < 0:
                out[i:] = [" "] * (len(value) - i)
                break
            out[i:end + len(dollar_tag)] = [" "] * (end + len(dollar_tag) - i)
            i = end + len(dollar_tag)
            dollar_tag = None
            continue
        if state == "line-comment":
            if value[i] in "\r\n":
                state = None
            else:
                out[i] = " "
            i += 1
            continue
        if state == "block-comment":
            out[i] = " "
            if value.startswith("*/", i):
                out[i : i + 2] = [" ", " "]
                state = None
                i += 2
            else:
                i += 1
            continue
        if state == "'":
            quote = state
            out[i] = " "
            if value[i] == quote:
                if i + 1 < len(value) and value[i + 1] == quote:
                    out[i + 1] = " "
                    i += 2
                    continue
                state = None
            elif value[i] == "\\" and i + 1 < len(value):
                out[i + 1] = " "
                i += 2
                continue
            i += 1
            continue
        if state in {'"', '`'} and preserve_identifiers:
            # Double-quoted and backtick-quoted SQL names are identifiers,
            # not string literals; retain their contents for DELETE matching.
            quote = state
            if value[i] == quote:
                out[i] = " "
                state = None
            i += 1
            continue
        if state in {'"', '`'}:
            out[i] = " "
            if value[i] == state:
                state = None
            i += 1
            continue
        # MySQL executable comments are code, not comments. Preserve their
        # body so `/*! DROP TABLE ... */` is classified like the server does.
        if dialect == "mysql" and value.startswith("/*!", i):
            i += 3
        elif dialect == "mysql" and value[i] == "#":
            out[i] = " "
            state = "line-comment"
            i += 1
        elif value.startswith("--", i):
            out[i : i + 2] = [" ", " "]
            state = "line-comment"
            i += 2
        elif value.startswith("/*", i):
            out[i : i + 2] = [" ", " "]
            state = "block-comment"
            i += 2
        elif value[i] == "$" and (match := re.match(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$", value[i:])):
            dollar_tag = match.group(0)
            out[i:i + len(dollar_tag)] = [" "] * len(dollar_tag)
            i += len(dollar_tag)
        elif value[i] == "[":
            close = value.find("]", i + 1)
            if close < 0:
                out[i:] = [" "] * (len(value) - i)
                break
            out[i:close + 1] = [" "] * (close + 1 - i)
            i = close + 1
        elif value[i] in "'\"`":
            out[i] = " "
            state = value[i]
            i += 1
        else:
            i += 1
    return "".join(out)


def sql_delete_without_where(value: str, dialect: str | None = None) -> bool:
    def split_statements(text: str) -> list[str]:
        statements: list[str] = []
        start = 0
        i = 0
        quote: str | None = None
        dollar: str | None = None
        comment: str | None = None
        while i < len(text):
            ch = text[i]
            if comment == "line":
                if ch in "\r\n":
                    comment = None
                i += 1
                continue
            if comment == "block":
                if text.startswith("*/", i):
                    comment = None
                    i += 2
                else:
                    i += 1
                continue
            if dollar:
                end = text.find(dollar, i)
                if end < 0:
                    return statements + [text[start:]]
                i = end + len(dollar)
                dollar = None
                continue
            if quote:
                if ch == "\\" and quote == "'":
                    i += 2
                    continue
                if ch == quote:
                    if i + 1 < len(text) and text[i + 1] == quote:
                        i += 2
                        continue
                    quote = None
                i += 1
                continue
            if ch in "'\"`":
                quote = ch
                i += 1
                continue
            if ch == "[":
                end = text.find("]", i + 1)
                i = len(text) if end < 0 else end + 1
                continue
            if ch == "$":
                match = re.match(r"\$(?:[A-Za-z_][A-Za-z0-9_]*)?\$", text[i:])
                if match:
                    dollar = match.group(0)
                    i += len(dollar)
                    continue
            if dialect == "mysql" and text.startswith("/*!", i):
                i += 3
                continue
            if dialect == "mysql" and text[i] == "#":
                comment = "line"
                i += 1
                continue
            if text.startswith("--", i):
                comment = "line"
                i += 2
                continue
            if text.startswith("/*", i):
                comment = "block"
                i += 2
                continue
            if ch == ";":
                statements.append(text[start:i])
                start = i + 1
            i += 1
        statements.append(text[start:])
        return statements

    def has_top_level_where(text: str) -> bool:
        cleaned_tail = sql_code(text)
        depth = 0
        for match in re.finditer(r"[()]|\bwhere\b", cleaned_tail, re.I):
            if match.group() == "(":
                depth += 1
            elif match.group() == ")":
                depth = max(0, depth - 1)
            elif depth == 0:
                return True
        return False

    for raw_statement in split_statements(value):
        # Locate DELETE only in the quote/comment-masked view so SQL-looking
        # text inside SELECT/RETURNING literals cannot become a command.
        cleaned = sql_code(raw_statement, dialect=dialect)
        for candidate in re.finditer(r"\bdelete\s+from\s+", cleaned, re.I):
            delete = re.match(
                r"\bdelete\s+from\s+(?:\"[^\"]+\"|`[^`]+`|\[[^\]]+\]|[^\s;]+)",
                raw_statement[candidate.start():], re.I,
            )
            if delete and not has_top_level_where(sql_code(
                    raw_statement[candidate.start() + delete.end():], dialect=dialect)):
                return True
    return False


def sql_schema_destructive(value: str, dialect: str | None = None) -> bool:
    return bool(re.search(r"\b(?:drop\s+(?:table|database)|truncate(?:\s+table)?)\b", sql_code(value, dialect=dialect), re.I))


def git_force_push(tokens: list[Token], index: int) -> bool:
    args = tokens[index + 1 :]
    subcommand = None
    i = 0
    while i < len(args):
        word = args[i].value
        if word in {"-C", "-c", "--config-env", "--git-dir", "--work-tree",
                    "--namespace", "--super-prefix"}:
            i += 2
            continue
        if word.startswith(("--config-env=", "--git-dir=", "--work-tree=",
                            "--namespace=", "--super-prefix=")):
            i += 1
            continue
        if not word.startswith("-"):
            subcommand = word
            break
        i += 1
    if subcommand != "push":
        return False
    return any(t.value in {"-f", "--force", "--force-with-lease"} or t.value.startswith("--force-with-lease=") for t in args[i + 1 :])


_SHORT_OPTION_ASSIGNMENT = re.compile(r"(?:^\s*|[;&|\n]\s*)([A-Za-z_][A-Za-z0-9_]*)=(?:\$)?([\"']?)(-[rRfF]+)\2(?=\s*;|\s|$)")


def expand_simple_option_assignments(command: str) -> str:
    """Resolve literal rm flags with shell-order assignment semantics."""
    events: list[tuple[int, str, str | None]] = []
    pattern = re.compile(
        r"(?:^|[;&|\n])\s*(?:(?:export|readonly)\s+)*"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*(\+=|=)\s*"
        r"((?:\$'[^']*'|'[^']*'|\"[^\"]*\"|[^\s;&|]+)*)"
    )
    for match in pattern.finditer(command):
        name, operator, expression = match.groups()
        pieces = re.findall(r"\$'([^']*)'|'([^']*)'|\"([^\"]*)\"|([^\s;&|]+)", expression)
        decoded = "".join(
            _decode_ansi_c(a) if a else b if b else c if c else d
            for a, b, c, d in pieces
        )
        decoded = re.sub(r"\\(.)", r"\1", decoded)
        previous = next((value for start, old_name, value in reversed(events)
                         if old_name == name and start <= match.start()), "")
        if operator == "+=":
            decoded = previous + decoded
        events.append((match.end(), name, decoded))

    # Assignment builtins accept multiple name=value words, and declare/
    # typeset are equivalent state updates for the later command in the same
    # shell list. Record every word rather than only the first one.
    builtin_pattern = re.compile(
        r"(?:^|[;&|\n])\s*(?:export|readonly|declare|typeset)\s+"
        r"((?:(?:[A-Za-z_][A-Za-z0-9_]*)\s*(?:\+=|=)\s*"
        r"(?:\$'[^']*'|'[^']*'|\"[^\"]*\"|[^\s;&|]+)\s*)+)"
    )
    assignment_word = re.compile(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*(\+=|=)\s*"
        r"(\$'[^']*'|'[^']*'|\"[^\"]*\"|[^\s;&|]+)"
    )
    for statement in builtin_pattern.finditer(command):
        for assignment in assignment_word.finditer(statement.group(1)):
            name, operator, expression = assignment.groups()
            pieces = re.findall(r"\$'([^']*)'|'([^']*)'|\"([^\"]*)\"|([^\s;&|]+)", expression)
            decoded = "".join(
                _decode_ansi_c(a) if a else b if b else c if c else d
                for a, b, c, d in pieces
            )
            decoded = re.sub(r"\\(.)", r"\1", decoded)
            absolute = statement.start(1) + assignment.start()
            previous = next((value for start, old_name, value in reversed(events)
                             if old_name == name and start <= absolute), "")
            if operator == "+=":
                decoded = (previous or "") + decoded
            events.append((statement.start(1) + assignment.end(), name, decoded))

    # `env name=value command ...` establishes the same literal value for the
    # child command. The recursive shell-wrapper path carries these assignment
    # tokens into the payload separately below.
    env_pattern = re.compile(
        r"(?:^|[;&|\n])\s*env\s+(?:-[^\s;&|]+\s+)*"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^\s;&|]+)"
    )
    for match in env_pattern.finditer(command):
        events.append((match.end(), match.group(1), match.group(2)))

    # Shell variables are stateful at the point of use. A later `unset` must
    # invalidate an earlier literal assignment rather than leaving a stale
    # value available to the rm classifier.
    for match in re.finditer(
        r"(?:^|[;&|\n])\s*unset\s+(?:(?:-[fv])\s+)*(?:--)?([A-Za-z_][A-Za-z0-9_]*)", command
    ):
        events.append((match.end(), match.group(1), None))
    events.sort(key=lambda event: event[0])

    def replace_use(match: re.Match[str]) -> str:
        name = match.group(1) or match.group(2)
        value = next((value for end, old_name, value in reversed(events)
                      if old_name == name and end <= match.start()), "__UNSET__")
        if value == "":
            return ""
        if value not in (None, "__UNSET__"):
            return value
        return match.group(0)

    # Apply expansion only outside single-quoted shell words. A regex-only
    # substitution cannot distinguish executable `$name` from literal text.
    variable = re.compile(r"\$(?:([A-Za-z_][A-Za-z0-9_]*)|\{([A-Za-z_][A-Za-z0-9_]*)\})")
    output: list[str] = []
    i = 0
    quote: str | None = None
    while i < len(command):
        ch = command[i]
        if quote == "'":
            output.append(ch)
            i += 1
            if ch == "'":
                quote = None
            continue
        if quote == '"':
            if ch == "\\" and i + 1 < len(command):
                output.extend((ch, command[i + 1]))
                i += 2
                continue
            match = variable.match(command, i)
            if match:
                output.append(replace_use(match))
                i = match.end()
                continue
            output.append(ch)
            i += 1
            if ch == '"':
                quote = None
            continue
        if ch in "'\"":
            quote = ch
            output.append(ch)
            i += 1
            continue
        if ch == "\\" and i + 1 < len(command):
            output.extend((ch, command[i + 1]))
            i += 2
            continue
        match = variable.match(command, i)
        if match:
            output.append(replace_use(match))
            i = match.end()
        else:
            output.append(ch)
            i += 1
    return "".join(output)


def piped_or_heredoc_sql_is_destructive(command: str) -> bool:
    """Inspect SQL text fed to sqlite3 through stdin rather than argv."""
    clients = {"sqlite3", "psql", "mysql", "sqlcmd"}

    def shell_command_parts(text: str) -> list[str]:
        parts: list[str] = []
        start = 0
        quote: str | None = None
        escaped = False
        index = 0
        while index < len(text):
            char = text[index]
            if escaped:
                escaped = False
            elif char == "\\" and quote != "'":
                escaped = True
            elif quote:
                if char == quote:
                    quote = None
            elif char in "'\"":
                quote = char
            elif char == ";" or char == "\n":
                parts.append(text[start:index])
                start = index + 1
            elif char in "&|" and index + 1 < len(text) and text[index + 1] == char:
                parts.append(text[start:index])
                start = index + 2
                index += 1
            elif char == "&" and (index == 0 or text[index - 1] != ">") and (index + 1 >= len(text) or text[index + 1] != ">"):
                parts.append(text[start:index])
                start = index + 1
            index += 1
        parts.append(text[start:])
        return parts

    def heredoc_count(text: str) -> int:
        count = 0
        quote: str | None = None
        i = 0
        while i < len(text):
            char = text[i]
            if quote:
                if char == "\\" and quote == '"':
                    i += 2
                    continue
                if char == quote:
                    quote = None
                i += 1
                continue
            if char in "'\"":
                quote = char
            elif text.startswith("<<", i) and not text.startswith("<<<", i):
                count += 1
                i += 2
                continue
            i += 1
        return count

    structural_command, _, _ = split_heredocs(command)
    heredoc_header = re.compile(r"<<-?\s*(?:\\.|'[^'\r\n]*'|\"[^\"\r\n]*\"|[^\s;|&<>])+")
    actual_headers: list[re.Match[str]] = []
    quote: str | None = None
    escaped = False
    index = 0
    while index < len(structural_command):
        char = structural_command[index]
        if escaped:
            escaped = False
        elif char == "\\" and quote != "'":
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif structural_command.startswith("<<", index) and not structural_command.startswith("<<<", index):
            header = heredoc_header.match(structural_command, index)
            if header:
                actual_headers.append(header)
                index = header.end()
                continue
        index += 1
    heredoc_bodies: list[str] = []
    header_index = 0
    while header_index < len(actual_headers):
        first = actual_headers[header_index]
        line_end = command.find("\n", first.start())
        if line_end < 0:
            break
        headers = [first]
        while header_index + len(headers) < len(actual_headers) and actual_headers[header_index + len(headers)].start() < line_end:
            headers.append(actual_headers[header_index + len(headers)])
        cursor = line_end + 1
        for header in headers:
            delimiter_start = header.start() + 2
            if structural_command[delimiter_start:header.end()].lstrip().startswith("-"):
                delimiter_start += len(structural_command[delimiter_start:header.end()]) - len(
                    structural_command[delimiter_start:header.end()].lstrip()
                ) + 1
            while delimiter_start < header.end() and structural_command[delimiter_start] in " \t":
                delimiter_start += 1
            delimiter, _, _ = _read_heredoc_delimiter(structural_command, delimiter_start)
            terminator = re.compile(
                r"^[ \t]*" + re.escape(delimiter) + r"[ \t]*(?=;|\r?$)", re.M
            ).search(command, cursor)
            if not terminator or terminator.start() < cursor:
                break
            heredoc_bodies.append(command[cursor:terminator.start()])
            cursor = terminator.end()
        header_index += len(headers)
    heredoc_index = 0
    for part in shell_command_parts(structural_command):
        if "|" not in part and "<<" not in part:
            continue
        part_heredocs = heredoc_count(part)
        payloads: list[str] = []
        last_pipe = part.rfind("|")
        last_segment = part[last_pipe + 1 :]
        last_segment_tokens = tokenize(last_segment)
        last_segment_name = command_name(last_segment_tokens[0])[0] if last_segment_tokens else None
        stdin_overridden = bool(re.search(r"(?<![<])<(?![<])\s*(?:/|[A-Za-z0-9_.~-]|<)", last_segment))
        if ("|" in part and last_segment_name in clients and not stdin_overridden
                and (part_heredocs == 0 or last_pipe > part.rfind("<<"))):
            left_side = part.rsplit("|", 1)[0]
            quoted_payloads = [value for _quote, value in re.findall(r"(['\"])(.*?)\1", left_side, re.S)]
            payloads.extend(quoted_payloads or [left_side])
        # Each pipeline segment owns its own redirections. Inspect every SQL
        # client segment, while honoring a later file/process-substitution
        # stdin redirect that supersedes its heredoc.
        segments = re.split(r"(?<!\|)\|(?!\|)", part)
        segment_counts = [heredoc_count(segment) for segment in segments]
        segment_cursor = heredoc_index
        for segment_number, segment in enumerate(segments):
            segment_count = segment_counts[segment_number]
            groups = tokenize(segment)
            names = [command_name(group)[0] for group in groups]
            last_name = next((name for name in reversed(names) if name in clients), None)
            # A SQL client need not be the last pipeline command. Its stdin is
            # still supplied by the immediately preceding segment in
            # `producer | sqlite3 | logger`; inspect that producer instead of
            # tying safety to the terminal pipeline segment.
            if last_name in clients and segment_number > 0:
                redirected = bool(re.search(
                    r"(?<![<])<(?![<])\s*(?:/|[A-Za-z0-9_.~-]|<)", segment
                ))
                if not redirected and not segment_counts[segment_number]:
                    upstream = segments[segment_number - 1]
                    # Reconstruct the producer's post-expansion argv words.
                    # Raw quote-fragment regexes miss shell concatenation such
                    # as `'DROP ''TABLE users;'` and backslash-escaped spaces.
                    producer_words = []
                    for producer_command in tokenize(upstream):
                        if len(producer_command) > 1:
                            producer_words.append(" ".join(
                                token.value for token in producer_command[1:]
                            ))
                    payloads.extend(producer_words or [upstream])
            if last_name in clients and (segment_count or (segment_number > 0 and segment_counts[segment_number - 1])):
                if segment_count:
                    last_heredoc = segment.rfind("<<")
                    after = segment[last_heredoc + 2 :]
                    body_index = segment_cursor + segment_count - 1
                else:
                    after = segment
                    body_index = segment_cursor - 1
                redirected = bool(re.search(r"(?<![<])<(?![<])\s*(?:/|[A-Za-z0-9_.~-]|<)", after))
                if not redirected and body_index < len(heredoc_bodies):
                    payloads.append(heredoc_bodies[body_index])
            segment_cursor += segment_count
        heredoc_index += part_heredocs
        if any(sql_delete_without_where(payload, dialect="mysql" if "mysql" in part else None)
               or sql_schema_destructive(payload, dialect="mysql" if "mysql" in part else None)
               for payload in payloads):
            return True
    return False


# is_destructive recurses into every substitution, wrapper payload, and -c
# string it finds. A real command never nests more than a few levels deep;
# an adversarial one can nest thousands, which previously blew Python's
# recursion limit and crashed -- and a crash exits non-zero, indistinguishable
# from "allowed", i.e. silently fails open on exactly the input designed to
# defeat analysis. Past this depth we fail closed instead.
_MAX_RECURSION_DEPTH = 50


def is_destructive(command: str, _depth: int = 0) -> bool:
    if _depth > _MAX_RECURSION_DEPTH:
        return True

    command = expand_simple_option_assignments(command)
    structural_command, heredoc_shell_payloads, heredoc_expansion_payloads = split_heredocs(command)

    if piped_or_heredoc_sql_is_destructive(command):
        return True

    # Command substitutions execute even when embedded in an otherwise benign
    # command. Quoted heredocs suppress expansion; unquoted heredocs do not.
    substitution_sources = [structural_command, *heredoc_expansion_payloads]
    if any(
        is_destructive(substitution, _depth + 1)
        for source in substitution_sources
        for substitution in shell_substitutions(source)
    ):
        return True

    # A shell fed a script via a heredoc/here-string executes it like a pipe.
    if any(is_destructive(payload, _depth + 1) for payload in heredoc_shell_payloads):
        return True
    if any(is_destructive(payload, _depth + 1) for payload in here_document_payloads(structural_command)):
        return True

    for tokens in tokenize(structural_command):
        name, index = command_name(tokens)
        if not name:
            continue
        # Common utility wrappers execute the remaining arguments as a command;
        # recursively classify that payload instead of treating the wrapper as
        # the terminal command name.
        for position, token in enumerate(tokens):
            wrapper = posixpath.basename(token.value)
            if wrapper in WRAPPER_VALUE_OPTIONS:
                value_opts = WRAPPER_VALUE_OPTIONS[wrapper]
                payload = tokens[position + 1 :]
                idx = 0
                while idx < len(payload) and payload[idx].value.startswith("-") and payload[idx].value != "-":
                    opt = payload[idx].value
                    if opt == "--":
                        idx += 1
                        break
                    if opt.startswith("--"):
                        optname, fused = opt.split("=", 1)[0], "=" in opt
                    else:
                        optname, fused = opt[:2], len(opt) > 2
                    idx += 1
                    if optname in value_opts and not fused:
                        idx += 1
                payload = payload[idx:]
                if wrapper == "timeout":
                    while payload and re.fullmatch(r"[0-9]+(?:\.[0-9]+)?(?:ms|s|m|h|d)?", payload[0].value):
                        payload = payload[1:]
                if payload and is_destructive(" ".join(item.value for item in payload), _depth + 1):
                    return True
        if name == "rm" and shell_rm_dangerous(tokens, index):
            return True
        if name == "git" and (git_force_push(tokens, index) or any(t.value == "--hard" for t in tokens[index + 1 :]) and any(t.value == "reset" for t in tokens[index + 1 :])):
            return True
        if name in {"halt", "shutdown"}:
            return True
        # Direct SQL entered as a command, and SQL passed to common clients.
        if name.lower() in {"delete", "drop", "truncate"}:
            statement = " ".join(t.value for t in tokens[index:])
            if name.lower() == "delete" and sql_delete_without_where(statement):
                return True
            if name.lower() in {"drop", "truncate"}:
                return True
        if name in {"psql", "mysql", "sqlite3", "sqlcmd"}:
            for statement in sql_client_statements(tokens, index):
                dialect = "mysql" if name == "mysql" else None
                if sql_delete_without_where(statement, dialect=dialect) or sql_schema_destructive(statement, dialect=dialect):
                    return True
        if name == "dd" and any(t.value.startswith(("if=/dev/zero", "if=/dev/random")) for t in tokens[index + 1 :]):
            return True
        if name == "mkfs" or name.startswith("mkfs."):
            return True
        if name == "init" and any(t.value == "0" for t in tokens[index + 1 :]):
            return True
        if name == "python" and any(t.value in {"-c", "-e"} for t in tokens[index + 1 :]):
            if any(re.search(r"(?:os\.system|subprocess)", t.value) for t in tokens[index + 1 :]):
                return True
        # A shell's -c string and eval's arguments are executable shell code,
        # unlike the same text passed to echo/printf as documentation. Scan for
        # shells after wrappers such as exec, timeout, nohup, nice, and xargs.
        for position, token in enumerate(tokens[index:], start=index):
            if posixpath.basename(token.value) in _SHELL_WORDS and position + 1 < len(tokens):
                shell_args = tokens[position + 1 :]
                for shell_position, shell_token in enumerate(shell_args):
                    option = shell_token.value
                    if option.startswith(("-c=", "--command=")):
                        payload = option.split("=", 1)[1]
                    elif (
                        option == "--command" or
                        (option.startswith("-") and not option.startswith("--") and "c" in option[1:])
                    ) and shell_position + 1 < len(shell_args):
                        # Shell flags are routinely clustered (-lc, -euxc); the
                        # command string is the following argv element.
                        payload = shell_args[shell_position + 1].value
                    else:
                        continue
                    # `bash -n -c` / `sh -n -c` parses without executing the
                    # command string. Keep substitution analysis active, but
                    # do not classify the inert -c payload as an execution.
                    no_exec = any(
                        item.value == "--noexec"
                        or (item.value.startswith("-") and not item.value.startswith("--")
                            and "n" in item.value[1:])
                        for item in shell_args[:shell_position + 1]
                    )
                    if no_exec:
                        break
                    inherited = [
                        item.value for item in tokens[:position]
                        if _ASSIGNMENT_RE.match(item.value)
                    ]
                    payload_source = " ".join([*inherited, payload])
                    if payload and is_destructive(payload_source, _depth + 1):
                        return True
                    break
        if name == "eval":
            payload = " ".join(token.value for token in tokens[index + 1 :])
            if payload and is_destructive(payload, _depth + 1):
                return True
        # find executes the command after -exec/-execdir; inspect its payload.
        if name == "find":
            for position, token in enumerate(tokens[index + 1 :], start=index + 1):
                if token.value in {"-exec", "-execdir"}:
                    payload = []
                    for item in tokens[position + 1 :]:
                        if item.value in {";", "+"}:
                            break
                        payload.append(item.value)
                    if payload and is_destructive(" ".join(payload), _depth + 1):
                        return True
    # Pipelines into a shell execute their stdin as code; fail closed. A shell
    # reading a <(...) process substitution as its script argument is exactly
    # as dangerous as being piped that same output directly.
    for segment in pipe_shell_targets(structural_command):
        seg_tokens = tokenize(segment)
        if seg_tokens and command_name(seg_tokens[0])[0] in _SHELL_WORDS:
            return True
    if shell_process_substitution_targets(structural_command):
        return True
    # Download-then-execute remains covered even without a direct pipe (e.g.
    # "curl -o f url; bash f").
    names = [command_name(tokens)[0] for tokens in tokenize(structural_command)]
    if any(n in {"curl", "wget"} for n in names) and any(n in _SHELL_WORDS for n in names):
        return True
    return False


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    return 0 if is_destructive(command) else 1


if __name__ == "__main__":
    raise SystemExit(main())
