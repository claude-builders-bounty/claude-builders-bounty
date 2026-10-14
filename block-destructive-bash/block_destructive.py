#!/usr/bin/env python3
"""block_destructive.py -- Claude Code PreToolUse hook that blocks destructive
Bash commands before they execute.

Wiring (see settings.snippet.json / install.sh):
    ~/.claude/settings.json -> hooks.PreToolUse, matcher "Bash",
    handler: python3 "~/.claude/hooks/block_destructive.py"

Behavior, per the Claude Code hooks API (docs.anthropic.com/en/docs/claude-code/hooks):
  * Reads the PreToolUse JSON payload from stdin.
  * Safe command  -> exit 0, prints nothing (zero output pollution).
  * Dangerous     -> appends one line to ~/.claude/hooks/blocked.log
                     (timestamp, cwd, command, rule), then exit 0 with a JSON
                     hookSpecificOutput carrying permissionDecision "deny" and
                     a permissionDecisionReason that Claude sees.
  * Any internal error / unparseable input -> exit 0 silently. A buggy hook
    must never break the user's session (fail-open on hook bugs, fail-closed
    only on positive matches).

Detection is token-based (shlex), not naive substring matching, so dangerous
words inside quoted strings (echo "rm -rf is dangerous") do not false-positive,
while wrappers (sudo/env/xargs), chained commands (&&, ;, |), and SQL fed to a
real database client (mysql -e "...", echo "..." | mysql, heredocs) do match.

Stdlib only. Python 3.8+.
"""

import json
import os
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Log location. Defaults to the path required by the bounty; the environment
# override exists so the test-suite can redirect it to a temp file.
LOG_PATH = Path(
    os.environ.get(
        "BLOCK_DESTRUCTIVE_LOG",
        str(Path.home() / ".claude" / "hooks" / "blocked.log"),
    )
)

# Commands that stand in front of the real program and should be skipped when
# locating it (e.g. "sudo rm -rf /", "env FOO=1 rm ...", "xargs rm").
WRAPPERS = {"sudo", "env", "time", "nice", "command", "builtin", "stdbuf", "nohup"}

# Recognised SQL clients. SQL statement checks only run when one of these is
# actually being executed (or raw SQL was pasted as the command), so merely
# *mentioning* SQL in echo/grep/cat does not trip the hook.
SQL_CLIENTS = {
    "mysql", "mariadb", "psql", "sqlite3", "duckdb",
    "mysqlsh", "sqlcmd", "clickhouse-client", "cqlsh",
}

# Operands that make even a non-force recursive rm catastrophic.
BROAD_RM_TARGETS = {
    "/", "/*", "~", "~/", "~/*", "$HOME", "${HOME}", "$HOME/*", ".", "..", "*",
}

ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

DROP_RE = re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[\"'`\w]", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)

FORCE_PUSH_FLAGS = {"-f", "--force", "--force-with-lease", "--force-if-includes"}


# ---------------------------------------------------------------------------
# Shell parsing helpers
# ---------------------------------------------------------------------------

def split_segments(command):
    """Split a shell command string into segments on &&, ||, ;, |, &.

    Returns a list of token lists, or None if the string cannot be tokenized
    (e.g. unbalanced quotes). Quoted text stays a single token, which is what
    keeps 'echo "rm -rf is dangerous"' safe.
    """
    try:
        # shlex.split() does not accept punctuation_chars; use the class API.
        lexer = shlex.shlex(command, posix=True, punctuation_chars="|&;")
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return None
    segments, current = [], []
    for tok in tokens:
        if tok and all(ch in "|&;" for ch in tok):
            if current:
                segments.append(current)
                current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def program_of(segment):
    """Return (program_basename, index) for a segment, skipping env
    assignments and wrapper commands (sudo, env, xargs, ...)."""
    i = 0
    while i < len(segment):
        tok = segment[i]
        if ENV_ASSIGN_RE.match(tok):
            i += 1
            continue
        base = os.path.basename(tok.lstrip("$`('\""))
        if base in WRAPPERS:
            i += 1
            continue
        if base == "xargs":
            i += 1
            while i < len(segment) and segment[i].startswith("-"):
                i += 1
            continue
        return base, i
    return None, i


# ---------------------------------------------------------------------------
# Rule checks -- each returns a human-readable rule name or None
# ---------------------------------------------------------------------------

def check_rm(segment, prog_idx):
    """Dangerous rm variants:
       - recursive + force, any target            (rm -rf, rm -fr, rm -r -f ...)
       - rm --no-preserve-root
       - recursive delete of /, ~, $HOME, ., ..   (even without -f)
       - forced delete of /, ~, $HOME             (even without -r)
    Plain 'rm -f file.txt' and 'rm -r somedir' are allowed (see README).
    """
    flags = set()
    operands = []
    seen_dashdash = False
    for tok in segment[prog_idx + 1:]:
        if not seen_dashdash and tok == "--":
            seen_dashdash = True
            continue
        if not seen_dashdash and tok.startswith("--"):
            name = tok[2:].split("=", 1)[0]
            if name == "recursive":
                flags.add("r")
            elif name == "force":
                flags.add("f")
            elif name == "no-preserve-root":
                return "rm --no-preserve-root"
            continue
        if not seen_dashdash and tok.startswith("-") and len(tok) > 1:
            flags.update(c for c in tok[1:] if c.isalpha())
            continue
        operands.append(tok)

    recursive = "r" in flags or "R" in flags
    force = "f" in flags
    if recursive and force:
        return "rm recursive+force (rm -rf)"
    if recursive and any(op in BROAD_RM_TARGETS for op in operands):
        return "rm recursive delete of a broad target (/, ~, $HOME, ., ..)"
    if force and any(op in {"/", "/*", "~", "~/*", "$HOME", "${HOME}"} for op in operands):
        return "rm forced delete of / or home directory"
    return None


def check_git(segment, prog_idx):
    """Force pushes rewrite shared remote history -> blocked. This includes
    --force-with-lease and --force-if-includes (see BUILD-NOTES.md for the
    reasoning) and the '+refspec' syntax."""
    rest = segment[prog_idx + 1:]
    i = 0
    while i < len(rest):
        tok = rest[i]
        if tok == "push":
            break
        if tok in ("-C", "-c", "--git-dir", "--work-tree"):
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return None  # some other git subcommand
    else:
        return None  # no subcommand found

    for arg in rest[i + 1:]:
        if arg in FORCE_PUSH_FLAGS or arg.startswith("--force-with-lease="):
            return "git force push (%s)" % arg
        if arg.startswith("+"):
            return "git force push (+refspec)"
        if arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]:
            return "git force push (%s)" % arg
    return None


def check_sql(raw_command):
    """Destructive SQL. Only invoked when a SQL client is being executed or
    raw SQL was pasted as the command (see sql_context_present)."""
    m = DROP_RE.search(raw_command)
    if m:
        return "SQL DROP %s" % m.group(1).upper()
    if TRUNCATE_RE.search(raw_command):
        return "SQL TRUNCATE"
    for m in DELETE_FROM_RE.finditer(raw_command):
        # The statement runs to the next ';' or newline; a WHERE anywhere in
        # that span makes it a targeted delete, which is allowed.
        statement = re.split(r"[;\n]", raw_command[m.end():], maxsplit=1)[0]
        if not WHERE_RE.search(statement):
            return "SQL DELETE FROM without a WHERE clause"
    return None


def sql_context_present(segments, programs):
    if any(p in SQL_CLIENTS for p in programs):
        return True
    # Raw SQL pasted straight into the shell ("DELETE FROM users" as a
    # "command"): the first token of some segment is the SQL keyword itself.
    for seg in segments:
        if seg and seg[0].upper() in ("DELETE", "DROP", "TRUNCATE"):
            return True
    return False


def find_violation(command):
    """Return the name of the first rule the command breaks, or None."""
    segments = split_segments(command)
    if segments is None:
        return None  # unparseable (bash would reject it too) -> fail open

    programs = []
    for seg in segments:
        prog, idx = program_of(seg)
        if prog is None:
            continue
        programs.append(prog)
        rule = None
        if prog == "rm":
            rule = check_rm(seg, idx)
        elif prog == "git":
            rule = check_git(seg, idx)
        if rule:
            return rule

    if sql_context_present(segments, programs):
        return check_sql(command)
    return None


# ---------------------------------------------------------------------------
# Logging + main
# ---------------------------------------------------------------------------

def log_block(cwd, command, rule):
    """Append one line: [timestamp] cwd=<project path> rule="..." command=...
    Logging failures never unblock the command (fail-closed on match)."""
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        flat = command.replace("\r", " ").replace("\n", "\\n")
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write('[%s] cwd=%s rule="%s" command=%s\n' % (stamp, cwd, rule, flat))
    except OSError:
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # no/invalid input -> nothing to judge -> allow

    if payload.get("tool_name") not in ("Bash", "PowerShell"):
        return 0
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command")
    if not isinstance(command, str) or not command.strip():
        return 0

    try:
        rule = find_violation(command)
    except Exception:
        return 0  # hook bug -> fail open, never break the session

    if rule is None:
        return 0  # safe: exit 0 and print nothing

    cwd = payload.get("cwd") or os.getcwd()
    log_block(cwd, command, rule)

    reason = (
        "Blocked by the block-destructive hook: this command matches the "
        "'%s' rule and was NOT executed. Commands of this kind permanently "
        "delete data or rewrite shared history, so the hook stops them before "
        "they run. Command: %s\n"
        "If the operation is genuinely intended, run it manually in a "
        "terminal outside Claude Code. To make it pass, narrow it instead: "
        "remove -r/-f from rm, drop --force from git push, or add a WHERE "
        "clause to the DELETE. Blocked attempts are logged to "
        "~/.claude/hooks/blocked.log." % (rule, command.strip())
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
