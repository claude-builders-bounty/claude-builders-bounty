#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads the PreToolUse JSON payload from stdin, inspects the Bash/PowerShell
command, and denies execution of commands that are irreversibly destructive:

  - ``rm -rf`` / ``rm -fr`` (any recursive + force removal)
  - ``rm -r`` targeting dangerous locations (/, ~, $HOME, *, ., .., /etc, ...)
  - ``git push --force`` / ``git push -f`` (use --force-with-lease instead)
  - ``DROP TABLE``, ``TRUNCATE`` (SQL schema destruction)
  - ``DELETE FROM <table>`` without a WHERE clause
  - ``mkfs``, ``dd ... of=/dev/...``, fork bombs, ``> /dev/sdX`` redirection

On a block it:
  1. Appends ``timestamp | cwd | command`` to ``~/.claude/hooks/blocked.log``
  2. Prints a JSON ``hookSpecificOutput`` decision (``permissionDecision: deny``)
     for modern Claude Code versions
  3. Prints a human-readable reason to stderr and exits 2, which older
     Claude Code versions treat as a block with the stderr text as the reason

On allow it exits 0 silently. Zero third-party dependencies (stdlib only).

Install: see README.md in this directory.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")

# ---------------------------------------------------------------------------
# Command parsing helpers
# ---------------------------------------------------------------------------

# Tokens that wrap a command without changing its meaning; strip them and
# re-examine what is actually being executed.
_WRAPPER_PREFIXES = ("sudo", "doas", "run0", "sg", "nice", "nohup", "stdbuf",
                     "timeout", "time", "command", "builtin", "env", "xargs")

# Assignments like FOO=bar that precede the real command.
_ENV_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=(\S+|\"[^\"]*\"|'[^']*')$")

# Split chained commands so `echo ok && rm -rf /` cannot smuggle a payload
# past the check. Handles &&, ||, ;, newlines and pipes.
_CHAIN_SPLIT_RE = re.compile(r"&&|\|\||[;\n]|(?<!\|)\|(?!\|)")


def _strip_wrappers(tokens):
    """Remove sudo/doas/env-assignment prefixes, return remaining tokens."""
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _WRAPPER_PREFIXES:
            # `env`/`timeout`/`nice` take VAR= assignments or -flags; skip them.
            i += 1
            while i < len(tokens) and (
                    _ENV_ASSIGN_RE.match(tokens[i]) or tokens[i].startswith("-")):
                i += 1
            continue
        if _ENV_ASSIGN_RE.match(tok):
            i += 1
            continue
        break
    return tokens[i:]


def _tokenize(segment):
    """Split a command segment into tokens, honouring simple quotes."""
    tokens, cur, quote = [], "", None
    for ch in segment:
        if quote:
            if ch == quote:
                quote = None
            else:
                cur += ch
        elif ch in ("'", '"'):
            quote = ch
        elif ch.isspace():
            if cur:
                tokens.append(cur)
                cur = ""
        else:
            cur += ch
    if cur:
        tokens.append(cur)
    return tokens


def _segments(command):
    """Yield (command_word, tokens) for each chained segment of a command."""
    for part in _CHAIN_SPLIT_RE.split(command):
        part = part.strip().strip("()")
        if not part:
            continue
        tokens = _strip_wrappers(_tokenize(part))
        if tokens:
            yield tokens[0].lower(), tokens


# ---------------------------------------------------------------------------
# Dangerous-target detection for `rm -r` (without -f)
# ---------------------------------------------------------------------------

_DANGEROUS_TARGETS = {
    "/", "/*", "~", "~/*", "$HOME", "$HOME/*", "${HOME}", ".", "./", "..",
    "../", "*", "/*",
}
_DANGEROUS_PREFIXES = (
    "/etc", "/usr", "/bin", "/sbin", "/var", "/opt", "/root", "/boot",
    "/dev", "/proc", "/sys", "/lib", "/home", "/private", "/System",
    "/Applications", "C:\\", "C:/",
)


def _is_dangerous_rm_target(target):
    """True if an rm target is a location that must never be removed."""
    if not target or target == "--":
        return True  # `rm -r` with no (or only `--`) target: refuse to guess
    t = target.strip("'\"")
    if t in _DANGEROUS_TARGETS:
        return True
    # $HOME / ${HOME} / ~ forms, possibly with trailing /*
    if re.match(r"^(~|\$HOME|\$\{HOME\})(/.*)?$", t):
        return True
    # Unquoted glob that could expand to everything
    if t == "*" or t.endswith("/*") and t.count("/") <= 1:
        return True
    for prefix in _DANGEROUS_PREFIXES:
        if t == prefix or t.startswith(prefix + "/"):
            return True
    return False


# ---------------------------------------------------------------------------
# Pattern checks: each returns a reason string, or None when clean
# ---------------------------------------------------------------------------

def _check_rm(word, tokens):
    if word != "rm":
        return None
    flags = set()
    saw_ddash = False
    targets = []
    for tok in tokens[1:]:
        if saw_ddash:
            targets.append(tok)
        elif tok == "--":
            saw_ddash = True
        elif tok.startswith("-") and len(tok) > 1 and not _ENV_ASSIGN_RE.match(tok):
            flags.update(ch for ch in tok[1:] if ch.isalpha())
        else:
            targets.append(tok)
    recursive = "r" in flags or "R" in flags
    force = "f" in flags
    if recursive and force:
        return ("'rm' with recursive (-r/-R) and force (-f) flags is blocked. "
                "It deletes without confirmation and without recovery. Ask the "
                "user to run it themselves, or remove the specific path with "
                "a scoped command after explicit user confirmation.")
    if recursive:
        for target in targets:
            if _is_dangerous_rm_target(target):
                return ("'rm -r' targeting '%s' is blocked: that location is "
                        "the filesystem root, home directory, or a system "
                        "directory." % target)
    return None


def _check_git_push(word, tokens):
    if word != "git" or len(tokens) < 2 or tokens[1] != "push":
        return None
    args = tokens[2:]
    if "--force-with-lease" in args:
        return None  # the safe variant: explicitly allowed
    if "--force" in args or "-f" in args:
        return ("'git push --force' is blocked: it rewrites shared history and "
                "can orphan teammates' work. Use 'git push --force-with-lease' "
                "instead, or ask the user to force-push manually.")
    return None


_SQL_DROP_RE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
_SQL_TRUNCATE_RE = re.compile(r"\btruncate\b", re.IGNORECASE)
_SQL_DELETE_RE = re.compile(r"\bdelete\s+from\s+([\"'`\[]?[\w.]+[\"'`\]]?)",
                            re.IGNORECASE)
_SQL_WHERE_RE = re.compile(r"\bwhere\b", re.IGNORECASE)


_SQL_CLIENTS = {
    "sqlite3", "sqlite", "psql", "mysql", "mariadb", "duckdb", "sqlcmd",
    "isql", "clickhouse-client",
}
_SQL_STMT_START_RE = re.compile(r"^\s*(drop|truncate|delete)\b", re.IGNORECASE)


def _check_sql(segment, word):
    # Only inspect text that is actually SQL: a SQL client invocation, or a
    # bare statement (e.g. a heredoc body). This keeps `echo 'do not DROP
    # TABLE'` and friends passing through untouched.
    if word == "truncate":
        return None  # coreutils truncate(1), not SQL
    sql_ctx = word in _SQL_CLIENTS or bool(_SQL_STMT_START_RE.match(segment))
    if not sql_ctx:
        return None
    if _SQL_DROP_RE.search(segment):
        return ("'DROP TABLE' is blocked: it irreversibly destroys schema and "
                "data. Ask the user to run schema changes manually.")
    if _SQL_TRUNCATE_RE.search(segment):
        return ("'TRUNCATE' is blocked: it irreversibly wipes a table. Ask the "
                "user to run it manually.")
    m = _SQL_DELETE_RE.search(segment)
    if m and not _SQL_WHERE_RE.search(segment[m.end():]):
        return ("'DELETE FROM %s' without a WHERE clause is blocked: it would "
                "delete every row. Add a WHERE clause scoping the rows, or ask "
                "the user to run it manually." % m.group(1))
    return None


def _check_system_destroy(segment, word):
    low = segment.lower()
    if re.search(r"\bmkfs(\.\w+)?\b", low):
        return ("'mkfs' is blocked: it formats a filesystem, destroying all "
                "data on the device. Ask the user to run it manually.")
    if word == "dd" and re.search(r"\bof=/dev/", low):
        return ("'dd ... of=/dev/...' is blocked: it writes raw bytes to a "
                "device. Ask the user to run it manually.")
    if re.search(r">\s*/dev/(sd[a-z]+|hd[a-z]+|nvme\d+n\d+|vd[a-z]+)", low):
        return ("Redirecting output to a raw disk device (/dev/...) is "
                "blocked: it corrupts the device. Ask the user to run it "
                "manually.")
    if re.search(r"\bchmod\b.*(-R|--recursive)\b.*\b777\b", low) and \
            re.search(r"(^|\s)/(\s|$)", segment):
        return ("'chmod -R 777 /' is blocked: it would make the entire "
                "filesystem world-writable. Ask the user to run it manually.")
    return None


_FORK_BOMB_RE = re.compile(r":\(\)\s*\{\s*:\|\s*:&\s*\}\s*;?\s*:")

# $() and backtick command substitution: inspect the inner command too.
_SUBST_RES = (re.compile(r"\$\(([^()]*)\)"), re.compile(r"`([^`]*)`"))


def _check_whole_command(command):
    """Checks that must see the un-split command text.

    The chain splitter breaks on `|` and `;`, which are part of fork-bomb
    syntax, so this runs before segmentation.
    """
    if _FORK_BOMB_RE.search(command):
        return ("Fork bomb ':(){ :|:& };:' is blocked: it would exhaust system "
                "resources and hang the machine.")
    for rx in _SUBST_RES:
        for inner in rx.findall(command):
            reason = find_block_reason(inner)
            if reason:
                return ("Blocked inside command substitution: %s" % reason)
    return None


def _check_powershell(word, tokens, segment):
    # Remove-Item is the PowerShell equivalent of rm.
    if word not in ("remove-item", "rm", "ri", "del", "erase", "rd"):
        return None
    joined = " ".join(tokens).lower()
    recurse = "-recurse" in joined
    force = "-force" in joined
    if recurse and force:
        return ("'Remove-Item -Recurse -Force' is blocked: it deletes without "
                "confirmation and without recovery. Ask the user to run it "
                "themselves.")
    if recurse and any(t in segment for t in ("C:\\", "C:/", "~", "$HOME",
                                              "$env:USERPROFILE", "*", "/")):
        return ("'Remove-Item -Recurse' targeting a root, home, or wildcard "
                "location is blocked.")
    return None


def _check_shell_exec(word, tokens, segment):
    # `sh -c "rm -rf /"` / `bash -c '...'` smuggling: inspect the -c payload.
    if word in ("sh", "bash", "zsh", "dash", "pwsh", "powershell"):
        try:
            c_idx = tokens.index("-c")
            payload = " ".join(tokens[c_idx + 1:])
            for reason in _scan_segment(payload):
                return ("Blocked inside '%s -c \"...\"': %s" % (word, reason))
        except ValueError:
            pass
    return None


def _scan_segment(segment):
    """Yield block reasons for one chained command segment."""
    word, tokens = next(_segments(segment), (None, []))
    if not word:
        return
    for check in (_check_rm, _check_git_push):
        reason = check(word, tokens)
        if reason:
            yield reason
    for check in (_check_system_destroy,):
        reason = check(segment, word)
        if reason:
            yield reason
    reason = _check_powershell(word, tokens, segment)
    if reason:
        yield reason
    reason = _check_shell_exec(word, tokens, segment)
    if reason:
        yield reason
    reason = _check_sql(segment, word)
    if reason:
        yield reason


def find_block_reason(command):
    """Return the first block reason for a full (possibly chained) command."""
    reason = _check_whole_command(command)
    if reason:
        return reason
    for part in _CHAIN_SPLIT_RE.split(command):
        part = part.strip()
        if not part:
            continue
        for reason in _scan_segment(part):
            return reason
    return None


# ---------------------------------------------------------------------------
# Logging + hook I/O
# ---------------------------------------------------------------------------

def log_blocked(command, cwd):
    """Append timestamp | cwd | command to the blocked-commands log."""
    try:
        os.makedirs(HOOK_DIR, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = "%s | cwd=%s | command=%s\n" % (ts, cwd, command.replace("\n", " "))
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line)
    except OSError:
        # Logging must never break the hook: the block still applies.
        pass


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.stderr.write("block-destructive-bash: could not parse hook JSON "
                         "from stdin; allowing command.\n")
        return 0

    tool_name = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")
    cwd = payload.get("cwd", "")

    if tool_name not in ("Bash", "PowerShell") or not command:
        return 0  # not a shell invocation: nothing to inspect

    reason = find_block_reason(command)
    if not reason:
        return 0

    log_blocked(command, cwd)

    decision = {
        "hookSpecificOutput": {
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
            "additionalContext": (
                "Blocked by the destructive-command guard "
                "(~/.claude/hooks/block-destructive-bash.py). "
                "The attempt was logged to ~/.claude/hooks/blocked.log."
            ),
        }
    }
    # JSON decision for modern Claude Code; stderr + exit 2 for older versions
    # (exit 2 routes as a deny with the stderr text as the reason).
    sys.stdout.write(json.dumps(decision) + "\n")
    sys.stderr.write("BLOCKED by destructive-command guard: %s\n" % reason)
    return 2


if __name__ == "__main__":
    sys.exit(main())
