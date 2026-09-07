#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads the PreToolUse event JSON from stdin (fields: tool_name,
tool_input.command, cwd), decides allow/deny, logs every blocked attempt
to ~/.claude/hooks/blocked.log, and communicates the decision back to
Claude Code.

Decision protocol (compatible with old and new Claude Code clients):
  - BLOCKED -> JSON deny object on stdout + human-readable reason on
    stderr + exit code 2 (blocking error). Either signal alone blocks
    the tool call; together they cover every client version.
  - ALLOWED -> exit code 0 with no output (silent; normal permission
    flow continues, so normal commands are never disturbed).

Blocked patterns (all detected anywhere in the command, including
chained commands joined by ; && || | newlines):
  1. rm_recursive      - any `rm` invocation with -r/-R/--recursive
                         (covers `rm -rf`, `rm -fr`, `rm -r`, sudo rm,
                         /bin/rm and quoted "rm"/'rm' forms ...)
  2. drop_table        - DROP [TEMPORARY] TABLE (case-insensitive)
  3. git_push_force    - `git push` with --force / --force=<..> / -f
                         or a `+<refspec>` force-prefix (e.g. +main,
                         +refs/heads/main)
                         (--force-with-lease and --force-if-includes
                         are explicitly ALLOWED as safe variants)
  4. truncate          - TRUNCATE (case-insensitive)
  5. delete_no_where   - DELETE FROM without a WHERE clause in the same
                         statement (case-insensitive; DELETE ... WHERE
                         is allowed)

Stdlib only, no dependencies. Works on Windows PowerShell, Linux, macOS
as long as `python`/`python3` is on PATH.

Usage:
  python hook.py                # run as Claude Code hook (reads stdin JSON)
  python hook.py --test         # run built-in self-tests (no pytest needed)
  python hook.py --check "cmd"  # check one command, print ALLOW/BLOCK + reason
"""

import datetime
import json
import os
import re
import shlex
import sys
from pathlib import Path

HOOK_NAME = "claude-hook-guard"

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# DROP [TEMPORARY] TABLE ... (case-insensitive)
_RE_DROP_TABLE = re.compile(r"\bDROP\s+(TEMPORARY\s+)?TABLE\b", re.IGNORECASE)

# TRUNCATE [TABLE] ... (case-insensitive)
_RE_TRUNCATE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)

# DELETE FROM ... / WHERE ... (case-insensitive, evaluated per statement)
_RE_DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
_RE_WHERE = re.compile(r"\bWHERE\b", re.IGNORECASE)

# rm invocation start: start-of-string or a shell separator (including `/`
# for absolute paths like /bin/rm and quotes for `"rm"`/`'rm'`),
# optionally preceded by `sudo ` (also covers `sudo -n rm`, `sudo -u x rm`
# via the looser sudo-with-flags form below).
_RE_RM_INVOKE = re.compile(
    r'''(?:^|[\s;&|(`$/\"'\n])\s*(?:sudo(?:\s+[-\w=]+)*\s+)?rm\b'''
)
# A recursive flag token inside a single rm invocation.
_RE_RM_RECURSIVE_FLAG = re.compile(
    r"(?:^|\s)(-[a-zA-Z]*[rR][a-zA-Z]*|--recursive)(?:\s|$|=)"
)

# git push segment detection (case-sensitive: git subcommands are lowercase).
_RE_GIT_PUSH = re.compile(r"\bgit\b[^\n;|&]*\bpush\b")
# A bare --force token that is NOT --force-with-lease / --force-if-includes.
# `--force(?![-\w])` matches `--force`, `--force=...`, `--force <...>` but
# not `--force-with-lease...` (next char after `force` is `-`).
_RE_GIT_LONG_FORCE = re.compile(r"--force(?![-\w])", re.IGNORECASE)
# A leading `+` on a push refspec forces the update without --force
# (e.g. `git push origin +main`, `git push origin +refs/heads/main`).
# Matches a `+ref` argument after start/whitespace/quote.
_RE_GIT_FORCE_REFSPEC = re.compile(r'''(?:^|[\s\"'])(\+[^\s\"']+)''')


def _split_shell_segments(command):
    """Split a shell command on separators so chained payloads are caught.

    e.g. "echo hi; rm -rf /" -> ["echo hi", " rm -rf /"].
    Keeps it simple (no full shell parsing) -- conservative by design.
    """
    return re.split(r"[;\n]+|\|\||\||&&", command)


def _check_rm(command):
    """Block any `rm` invocation carrying a recursive flag."""
    for m in _RE_RM_INVOKE.finditer(" " + command):
        # Look at the rest of this rm invocation (up to the next separator).
        tail = command[m.end():]
        tail = re.split(r"[;\n|&]", tail, maxsplit=1)[0]
        # Also include flags that appear before the end of the tail; the
        # leading space guarantees (^|\\s) anchoring works.
        if _RE_RM_RECURSIVE_FLAG.search(" " + tail):
            return True
    return False


def _segment_is_git_push(segment):
    return bool(_RE_GIT_PUSH.search(segment))


def _check_git_push_force(command):
    """Block `git push --force` / `git push -f`, allow safe variants.

    Allowed (safe-ish, explicitly): --force-with-lease,
    --force-if-includes (any value form). Everything else matching a
    bare --force token or a short -f flag inside a git-push segment
    is blocked.
    """
    for segment in _split_shell_segments(command):
        if not _segment_is_git_push(segment):
            continue
        # 1) long form: --force (but not --force-with-lease/if-includes,
        #    which the negative lookahead already excludes).
        if _RE_GIT_LONG_FORCE.search(segment):
            return True
        # 2) short form: standalone/combined -f flag, e.g. -f, -vf, -fv.
        #    Tokenize safely; fall back to a regex on token failure.
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            tokens = segment.split()
        for tok in tokens:
            if tok.startswith("--"):
                continue  # long flags handled above
            if re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", tok):
                # tok is a short-flag bundle containing f (e.g. -f, -vf).
                # Exclude the `git`/`push` words themselves (no leading -).
                return True
    return False


def _check_git_push_plus(command):
    """Block `git push` with a `+<refspec>` force-prefix shorthand.

    e.g. `git push origin +main`, `git push origin +refs/heads/main`.
    The leading `+` forces the ref update without any --force flag, so it
    must be treated as git_push_force. Token-based (shlex) so quoted forms
    like `"+main"` are also caught; falls back to a plain-text scan for
    unbalanced quoting.
    """
    for segment in _split_shell_segments(command):
        if not _segment_is_git_push(segment):
            continue
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            tokens = segment.split()
        for tok in tokens:
            if tok.startswith("+") and len(tok) > 1:
                return True
        # Fallback for unbalanced quotes etc.: plain-text `+ref` scan.
        # Guard against `a+b` arithmetic by re-checking whitespace-split
        # tokens stripped of surrounding quotes/parens.
        if _RE_GIT_FORCE_REFSPEC.search(segment):
            for tok in segment.split():
                t = tok.strip("();").lstrip("\"'")
                if t.startswith("+") and len(t) > 1:
                    return True
    return False


def _check_delete_without_where(command):
    """Block DELETE FROM statements that lack a WHERE clause.

    Split on ';' so `DELETE ... WHERE ...; DELETE FROM logs` still blocks
    on the second statement. A statement is only examined if it contains
    DELETE FROM; statements with WHERE anywhere after DELETE are allowed.
    """
    for statement in re.split(r";", command):
        if _RE_DELETE_FROM.search(statement):
            if not _RE_WHERE.search(statement):
                return True
    return False


# Human-readable reasons fed back to Claude (stderr + JSON deny reason).
REASONS = {
    "rm_recursive": (
        "Blocked: recursive `rm` (`rm -r`/`-R`/`--recursive`, including `rm -rf`) "
        "is not allowed because it can irreversibly delete large directory trees. "
        "Delete specific files without a recursive flag instead (e.g. `rm file.txt`), "
        "or ask the user to run the recursive delete themselves."
    ),
    "drop_table": (
        "Blocked: `DROP TABLE` irreversibly deletes a whole database table and its data. "
        "This must be run by a human, not the agent. If a schema change is needed, "
        "propose the SQL and ask for confirmation."
    ),
    "git_push_force": (
        "Blocked: `git push --force` (or `-f`, or a `+<refspec>` prefix like "
        "`+main`) rewrites shared history and can "
        "permanently discard other people's commits. Use `git push --force-with-lease` "
        "if a force-push is truly needed, or ask the user to force-push themselves."
    ),
    "truncate": (
        "Blocked: `TRUNCATE` instantly wipes every row of a table (often without "
        "logging individual deletes) and cannot be undone. This must be run by a "
        "human. Propose the statement and ask for confirmation instead."
    ),
    "delete_no_where": (
        "Blocked: `DELETE FROM` without a `WHERE` clause would delete every row in "
        "the table. Add a restrictive `WHERE` clause (e.g. `DELETE FROM t WHERE id = ...`) "
        "or ask the user to confirm the full-table wipe."
    ),
}


def check_command(command):
    """Return (blocked: bool, rule: str|None, reason: str|None)."""
    if not command or not command.strip():
        return False, None, None
    if _check_rm(command):
        return True, "rm_recursive", REASONS["rm_recursive"]
    if _RE_DROP_TABLE.search(command):
        return True, "drop_table", REASONS["drop_table"]
    if _check_git_push_force(command):
        return True, "git_push_force", REASONS["git_push_force"]
    if _check_git_push_plus(command):
        return True, "git_push_force", REASONS["git_push_force"]
    if _RE_TRUNCATE.search(command):
        return True, "truncate", REASONS["truncate"]
    if _check_delete_without_where(command):
        return True, "delete_no_where", REASONS["delete_no_where"]
    return False, None, None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_log_path():
    """Blocked-attempt log file. Overridable via CLAUDE_HOOK_BLOCKED_LOG."""
    override = os.environ.get("CLAUDE_HOOK_BLOCKED_LOG")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked(command, cwd, rule):
    """Append one line with timestamp, command, and project path.

    Never raises: logging must never break the hook decision path.
    Returns the log path written to (or None on failure).
    """
    try:
        path = get_log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        safe_cmd = " ".join(str(command).split())  # collapse whitespace/newlines
        line = f"[{ts}] BLOCKED rule={rule} cwd={cwd} command={safe_cmd}\n"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return path
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Hook I/O
# ---------------------------------------------------------------------------

def parse_hook_input(raw):
    """Extract (command, cwd) from PreToolUse stdin JSON. Never raises."""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, AttributeError):
        return "", os.getcwd()
    if not isinstance(data, dict):
        return "", os.getcwd()
    tool_input = data.get("tool_input", {})
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
    elif isinstance(tool_input, str):
        command = tool_input
    else:
        command = ""
    cwd = data.get("cwd") or data.get("working_directory") or os.getcwd()
    return str(command or ""), str(cwd or os.getcwd())


def deny_output(reason):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def handle_command(command, cwd):
    """Core decision + side effects. Returns process exit code."""
    blocked, rule, reason = check_command(command)
    if not blocked:
        return 0
    log_blocked(command, cwd, rule)
    # Structured decision for new clients (stdout) + plain message (stderr)
    # so the reason reaches Claude on every client version. Exit 2 is the
    # universal block signal.
    sys.stdout.write(json.dumps(deny_output(reason)))
    sys.stdout.write("\n")
    sys.stdout.flush()
    sys.stderr.write(f"[{HOOK_NAME}] {reason}\n")
    sys.stderr.flush()
    return 2


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--help" in argv or "-h" in argv:
        sys.stdout.write(str(__doc__ or "") + "\n")
        return 0
    if "--test" in argv:
        return run_self_tests()
    if "--check" in argv:
        idx = argv.index("--check")
        cmd = argv[idx + 1] if idx + 1 < len(argv) else ""
        blocked, rule, reason = check_command(cmd)
        sys.stdout.write(f"{'BLOCK' if blocked else 'ALLOW'} rule={rule} {reason or ''}\n")
        return 2 if blocked else 0
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    command, cwd = parse_hook_input(raw)
    # No command (e.g. non-Bash tool, empty input): stay silent, allow.
    if not command:
        return 0
    return handle_command(command, cwd)


# ---------------------------------------------------------------------------
# Built-in self-tests (python hook.py --test; no pytest required)
# ---------------------------------------------------------------------------

SELF_TESTS = [
    # (command, should_block, label)
    ("rm -rf /", True, "rm -rf root"),
    ("rm -rf ./build", True, "rm -rf relative dir also blocked (conservative)"),
    ("rm -fr /tmp/x", True, "rm -fr flag order"),
    ("rm -r mydir", True, "rm -r"),
    ("rm -R mydir", True, "rm -R"),
    ("rm --recursive somedir", True, "rm --recursive"),
    ("sudo rm -rf /tmp/x", True, "sudo rm -rf"),
    ("/bin/rm -rf /tmp/x", True, "/bin/rm absolute path"),
    ('"rm" -rf /tmp/x', True, 'quoted "rm"'),
    ("'rm' -rf /tmp/x", True, "quoted 'rm'"),
    ("sudo /bin/rm -rf /tmp/x", True, "sudo /bin/rm"),
    ("echo hi; rm -rf /tmp/x", True, "chained rm -rf after ;"),
    ("echo hi && rm -rf /tmp/x", True, "chained rm -rf after &&"),
    ("rm file.txt", False, "plain rm allowed"),
    ("rm -f file.txt", False, "rm -f without recursive allowed"),
    ("rm -i file.txt", False, "rm -i allowed"),
    ("DROP TABLE users", True, "DROP TABLE upper"),
    ("drop table users", True, "drop table lower (case-insensitive)"),
    ("Drop Temporary Table t", True, "DROP TEMPORARY TABLE mixed case"),
    ("SELECT * FROM users", False, "SELECT untouched"),
    ("TRUNCATE TABLE users", True, "TRUNCATE TABLE upper"),
    ("truncate users", True, "truncate lower (case-insensitive)"),
    ("git push --force origin main", True, "git push --force"),
    ("git push -f origin main", True, "git push -f short flag"),
    ("git push --force origin main && echo done", True, "chained force push"),
    ("git push origin +main", True, "git push +refspec shorthand"),
    ("git push origin +refs/heads/main", True, "git push +full refspec"),
    ('git push origin "+main"', True, 'git push quoted "+main"'),
    ("git push --force-with-lease origin main", False, "force-with-lease allowed"),
    ("git push --force-if-includes origin main", False, "force-if-includes allowed"),
    ("git push origin main", False, "plain git push allowed"),
    ("git status", False, "git status allowed"),
    ("git pull --force", False, "only push --force blocked, pull untouched"),
    ("DELETE FROM users", True, "DELETE without WHERE"),
    ("delete from users", True, "delete lowercase without WHERE"),
    ("DELETE FROM users WHERE id = 1", False, "DELETE with WHERE allowed"),
    ("delete from users where id=1", False, "delete lowercase with WHERE allowed"),
    ("DELETE FROM a WHERE x=1; DELETE FROM b", True, "second stmt w/o WHERE blocks"),
    ("ls -la", False, "ls allowed"),
    ("npm test", False, "npm test allowed"),
    ("echo hello", False, "echo allowed"),
    ("mkdir -p build && npm run build", False, "build chain allowed"),
    ("grep -rf pattern .", False, "grep -r... is not rm (no false positive)"),
    ("", False, "empty allowed"),
]


def run_self_tests():
    failures = 0
    for command, should_block, label in SELF_TESTS:
        blocked, rule, _ = check_command(command)
        ok = blocked == should_block
        status = "PASS" if ok else "FAIL"
        if not ok:
            failures += 1
        sys.stdout.write(
            f"[{status}] expect={'BLOCK' if should_block else 'ALLOW'} "
            f"got={'BLOCK' if blocked else 'ALLOW'} rule={rule} :: {label} :: {command!r}\n"
        )
    # Logging smoke test into a temp file (never touches the real log).
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        tmp = str(Path(td) / "blocked.log")
        os.environ["CLAUDE_HOOK_BLOCKED_LOG"] = tmp
        try:
            handle_command("rm -rf /", "/tmp/proj")
            content = Path(tmp).read_text(encoding="utf-8")
            assert "rm -rf /" in content and "/tmp/proj" in content and "rule=" in content
            sys.stdout.write("[PASS] logging writes timestamp+command+cwd :: blocked.log\n")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            sys.stdout.write(f"[FAIL] logging smoke test: {exc}\n")
        finally:
            os.environ.pop("CLAUDE_HOOK_BLOCKED_LOG", None)
    total = len(SELF_TESTS) + 1
    sys.stdout.write(f"\n{total - failures}/{total} self-tests passed\n")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
