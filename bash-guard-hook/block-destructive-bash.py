#!/usr/bin/env python3
"""block-destructive-bash.py -- Claude Code PreToolUse hook.

Blocks Bash commands that are likely destructive before Claude Code runs them:

  * ``rm -rf``            (recursive, forced delete)
  * ``DROP TABLE``        (SQL -- drops a table and all its data)
  * ``git push --force``  (rewrites shared history; ``-f`` too)
  * ``TRUNCATE``          (SQL -- empties a table)
  * ``DELETE FROM`` without a ``WHERE`` clause (deletes every row)

Protocol (Claude Code PreToolUse hook):
  * The tool-call JSON is read from stdin.
  * Exit 0  -> allow the command (silent).
  * Exit 2  -> block the command; the message on stderr is shown to Claude.
  * Every blocked attempt is appended to ``~/.claude/hooks/blocked.log``
    (override with the ``BASH_GUARD_LOG`` environment variable).

False-positive care:
  * ``rm -rf`` / ``git push --force`` inside a quoted string or a comment
    are not treated as commands (the shell would not run them either).
  * ``DELETE FROM ... WHERE ...`` is allowed; only a WHERE-less DELETE
    is blocked.
  * The ``truncate`` file utility (``truncate -s 0 file.log``) is not
    blocked -- only SQL ``TRUNCATE`` is.
  * ``git push --force-with-lease`` (the safe variant) is allowed.

Only the Python standard library is used. No network access, no dependencies.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Pattern explanations (shown to Claude when a command is blocked)
# ---------------------------------------------------------------------------

PATTERN_INFO = {
    "rm -rf": (
        "`rm -rf` recursively and forcibly deletes files and directories. "
        "There is no undo -- deleted files do not go to trash.",
        "Delete a specific path after listing it first (`ls <path>` then "
        "`rm <path>`), or move it aside instead of deleting it.",
    ),
    "DROP TABLE": (
        "`DROP TABLE` permanently drops a database table and all of its data.",
        "Back the table up first, or use a migration that renames or "
        "archives the table instead of dropping it.",
    ),
    "git push --force": (
        "`git push --force` rewrites shared history -- commits other people "
        "have already pulled can be lost.",
        "Use `git push --force-with-lease`, which refuses to overwrite work "
        "someone else pushed first.",
    ),
    "TRUNCATE": (
        "`TRUNCATE` instantly empties a table -- every row is gone at once.",
        "Delete with a `WHERE` clause instead, or back the table up first.",
    ),
    "DELETE FROM without WHERE": (
        "`DELETE FROM` without a `WHERE` clause deletes every row in the table.",
        "Add a `WHERE` clause that limits the rows, or run a `SELECT` with "
        "the same `WHERE` first to preview what would be deleted.",
    ),
}

# ---------------------------------------------------------------------------
# Shell-aware views of the command
# ---------------------------------------------------------------------------

ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


def split_views(command):
    """Split a command into two views.

    ``code``: comments removed and every quoted string replaced by a single
    space.  Used to spot real shell commands (``rm``, ``git``) -- a pattern
    inside quotes or a comment is not something the shell would run.

    ``with_strings``: comments removed but quoted strings kept intact.  Used
    for SQL patterns, which are normally passed as a string argument to a
    database client (``psql -c "DROP TABLE users"``) and are destructive
    exactly in that form.
    """
    code = []
    with_strings = []
    i, n = 0, len(command)
    in_single = False
    in_double = False
    while i < n:
        ch = command[i]
        if in_single:
            with_strings.append(ch)
            if ch == "'":
                in_single = False
            i += 1
            continue
        if in_double:
            if ch == "\\" and i + 1 < n:
                with_strings.append(command[i:i + 2])
                i += 2
                continue
            with_strings.append(ch)
            if ch == '"':
                in_double = False
            i += 1
            continue
        # Not inside any quote.
        if ch == "'":
            in_single = True
            with_strings.append(ch)
            code.append(" ")
            i += 1
            continue
        if ch == '"':
            in_double = True
            with_strings.append(ch)
            code.append(" ")
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            # Escaped character: keep it in both views, do not treat it as
            # a quote or a comment marker.
            with_strings.append(command[i:i + 2])
            code.append(command[i:i + 2])
            i += 2
            continue
        if ch == "#":
            prev = command[i - 1] if i > 0 else ""
            if i == 0 or prev in " \t\r\n;&|(":
                # Comment: skip to end of line.
                j = command.find("\n", i)
                if j == -1:
                    break
                with_strings.append("\n")
                code.append("\n")
                i = j + 1
                continue
            with_strings.append(ch)
            code.append(ch)
            i += 1
            continue
        with_strings.append(ch)
        code.append(ch)
        i += 1
    return "".join(code), "".join(with_strings)


# ---------------------------------------------------------------------------
# Tokeniser (operates on the ``code`` view, where quotes are already gone)
# ---------------------------------------------------------------------------

OPERATORS = {"&&", "||", ">>", "<<", ">&", "|&", ";;"}
SINGLE_OPS = set(";&|()<>`")
SEPARATORS = {"\n", ";", "&&", "||", "|", "&", "(", "`", ";;", "|&"}


def tokenize(code):
    """Split the ``code`` view into ("word", text) / ("op", text) tokens."""
    tokens = []
    buf = []
    i, n = 0, len(code)

    def flush():
        if buf:
            tokens.append(("word", "".join(buf)))
            buf.clear()

    while i < n:
        ch = code[i]
        if ch in " \t\r\n":
            flush()
            if ch == "\n":
                tokens.append(("op", "\n"))
            i += 1
            continue
        if ch == "\\" and i + 1 < n:
            buf.append(code[i:i + 2])
            i += 2
            continue
        if code[i:i + 2] in OPERATORS:
            flush()
            tokens.append(("op", code[i:i + 2]))
            i += 2
            continue
        if ch in SINGLE_OPS:
            flush()
            tokens.append(("op", ch))
            i += 1
            continue
        buf.append(ch)
        i += 1
    flush()
    return tokens


# ---------------------------------------------------------------------------
# Which words are real commands (not arguments, strings or comments)
# ---------------------------------------------------------------------------

PREFIX_COMMANDS = {"sudo", "time", "command", "builtin", "env", "nice", "xargs"}
PREFIX_VALUE_FLAGS = {
    "-u", "-g", "-h", "-p", "-U", "-C", "-c",
    "--user", "--group", "--host", "--prompt", "--chdir",
}


def _command_after_prefix(tokens, i):
    """Index of the command word that follows a prefix (sudo, env, ...) at i.

    Skips the prefix's own flags (and their values) and VAR= assignments.
    Returns None if no command word follows.
    """
    j = i + 1
    while j < len(tokens):
        kind, text = tokens[j]
        if kind == "op":
            return None
        if text == "--":
            j += 1
            if j < len(tokens) and tokens[j][0] == "word":
                return j
            return None
        if text.startswith("-") and text != "-":
            j += 2 if text in PREFIX_VALUE_FLAGS else 1
            continue
        if ASSIGN_RE.match(text):
            j += 1
            continue
        return j
    return None


def _mark_xargs_command(tokens, positions, i):
    """Mark the command word that ``xargs`` at index i will run."""
    j = i + 1
    while j < len(tokens):
        kind, text = tokens[j]
        if kind == "op":
            return
        if text.startswith("-") and text != "-":
            j += 2 if re.match(r"^-(I|n|P|s)$", text) else 1
            continue
        positions.add(j)
        return


def command_positions(tokens):
    """Indices of words that are real commands.

    A word is a command when it starts a simple command (first word, or
    after ``;``, ``&&``, ``||``, ``|``, ``&``, ``(``, a newline or a
    backtick), when it follows a prefix such as ``sudo``/``env``, or when
    it is the command run by ``find ... -exec`` / ``xargs``.
    """
    positions = set()
    expect_command = True
    i = 0
    while i < len(tokens):
        kind, text = tokens[i]
        if kind == "op":
            if text in SEPARATORS:
                expect_command = True
            i += 1
            continue
        # Word token.
        if expect_command:
            if ASSIGN_RE.match(text):
                i += 1
                continue
            positions.add(i)
            if text in PREFIX_COMMANDS:
                if text == "xargs":
                    _mark_xargs_command(tokens, positions, i)
                    expect_command = False
                else:
                    cmd_idx = _command_after_prefix(tokens, i)
                    if cmd_idx is not None:
                        positions.add(cmd_idx)
                    expect_command = False
            else:
                expect_command = False
            i += 1
            continue
        # Not expecting a command: look for commands run by other commands.
        if text in ("-exec", "-execdir"):
            j = i + 1
            if j < len(tokens) and tokens[j][0] == "word":
                positions.add(j)
        elif text == "xargs":
            _mark_xargs_command(tokens, positions, i)
        i += 1
    return positions


# ---------------------------------------------------------------------------
# Pattern checks
# ---------------------------------------------------------------------------

def check_rm(tokens, positions):
    """Block ``rm`` with both recursive and force flags."""
    for idx in sorted(positions):
        if tokens[idx][1] != "rm":
            continue
        recursive = False
        force = False
        j = idx + 1
        while j < len(tokens):
            kind, text = tokens[j]
            if kind == "op" or text == "--":
                break
            if text.startswith("-") and text != "-":
                if text.startswith("--"):
                    if text == "--recursive":
                        recursive = True
                    elif text == "--force":
                        force = True
                else:
                    flags = text[1:]
                    if "r" in flags or "R" in flags:
                        recursive = True
                    if "f" in flags:
                        force = True
            j += 1
        if recursive and force:
            return "rm -rf"
    return None


GIT_GLOBAL_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}


def check_git_push(tokens, positions):
    """Block ``git push --force`` / ``git push -f`` (not --force-with-lease)."""
    for idx in sorted(positions):
        if tokens[idx][1] != "git":
            continue
        # Find the subcommand, skipping git's own global flags.
        j = idx + 1
        push_idx = None
        while j < len(tokens):
            kind, text = tokens[j]
            if kind == "op":
                break
            if text in GIT_GLOBAL_VALUE_FLAGS:
                j += 1 if "=" in text else 2
                continue
            if text.startswith("-"):
                j += 1
                continue
            if text == "push":
                push_idx = j
            break
        if push_idx is None:
            continue
        # Scan everything after `push` for a force flag.
        k = push_idx + 1
        while k < len(tokens):
            kind, text = tokens[k]
            if kind == "op":
                break
            if text in ("--force", "-f"):
                return "git push --force"
            k += 1
    return None


def _truncate_in_quotes(view):
    """True if a bare TRUNCATE appears inside a quoted string (SQL payload)."""
    i, n = 0, len(view)
    while i < n:
        ch = view[i]
        if ch in ("'", '"'):
            quote = ch
            j = i + 1
            while j < n:
                if quote == '"' and view[j] == "\\" and j + 1 < n:
                    j += 2
                    continue
                if view[j] == quote:
                    break
                j += 1
            region = view[i + 1:j]
            if re.search(r"\bTRUNCATE\b", region, re.IGNORECASE):
                return True
            i = j + 1
            continue
        i += 1
    return False


def check_sql(view):
    """Block SQL patterns in the comment-stripped view (quotes kept)."""
    if re.search(r"\bDROP\s+TABLE\b", view, re.IGNORECASE):
        return "DROP TABLE"
    if re.search(r"\bTRUNCATE\s+TABLE\b", view, re.IGNORECASE):
        return "TRUNCATE"
    if _truncate_in_quotes(view):
        return "TRUNCATE"
    for match in re.finditer(r"\bDELETE\s+FROM\b", view, re.IGNORECASE):
        segment = view[match.end():]
        cut = len(segment)
        for term in (";", "\n"):
            pos = segment.find(term)
            if pos != -1:
                cut = min(cut, pos)
        segment = segment[:cut]
        if not re.search(r"\bWHERE\b", segment, re.IGNORECASE):
            return "DELETE FROM without WHERE"
    return None


def find_destructive(command):
    """Return a list of matched pattern names, or [] if the command is safe."""
    code, with_strings = split_views(command)
    tokens = tokenize(code)
    positions = command_positions(tokens)
    reasons = []
    for check in (lambda: check_rm(tokens, positions),
                  lambda: check_git_push(tokens, positions),
                  lambda: check_sql(with_strings)):
        reason = check()
        if reason is not None:
            reasons.append(reason)
    return reasons


# ---------------------------------------------------------------------------
# Logging and messaging
# ---------------------------------------------------------------------------

def log_path():
    return os.environ.get("BASH_GUARD_LOG") or os.path.expanduser(
        "~/.claude/hooks/blocked.log"
    )


def log_block(reasons, command, cwd):
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = (
        f"{timestamp} | BLOCKED | patterns={', '.join(reasons)} "
        f"| cwd={cwd} | command={command}\n"
    )
    try:
        path = log_path()
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass  # Logging must never stop the block from happening.


def block_message(command, reasons):
    lines = [
        "BLOCKED by bash-guard-hook: this Bash command looks destructive, "
        "so it was not run.",
        "",
        f"Command: {command}",
        "",
    ]
    for reason in reasons:
        why, alternative = PATTERN_INFO[reason]
        lines.append(f"Matched pattern: {reason}")
        lines.append(f"Why it is blocked: {why}")
        lines.append(f"Safer alternative: {alternative}")
        lines.append("")
    lines.append(
        "If you really intend to run this, ask the user to confirm it first, "
        "or run it yourself in a terminal outside this session."
    )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Hook entry point
# ---------------------------------------------------------------------------

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # Malformed input: fail open, never break the agent.
    if not isinstance(payload, dict):
        sys.exit(0)

    tool_name = payload.get("tool_name")
    if tool_name is not None and tool_name != "Bash":
        sys.exit(0)  # Only Bash tool calls are relevant.

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd() or "unknown"

    reasons = find_destructive(command)
    if not reasons:
        sys.exit(0)

    log_block(reasons, command, cwd)
    sys.stderr.write(block_message(command, reasons))
    sys.exit(2)


if __name__ == "__main__":
    main()
