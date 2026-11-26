#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: block destructive bash commands.

Bounty: claude-builders-bounty/claude-builders-bounty Issue #3 — $100 (Opire)
https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3

Blocks (before execution):
  * ``rm -rf`` and variants (``rm -fr``, ``rm -r -f``, ``rm --recursive --force``,
    ``sudo rm -rf ...``), and ``rm -r`` targeting /, ~, * or .
  * ``DROP TABLE`` (any case, including ``DROP TABLE IF EXISTS``)
  * ``git push --force`` / ``git push -f``  (``--force-with-lease`` is ALLOWED —
    it is the safe alternative, so it is explicitly not blocked)
  * ``TRUNCATE`` (``TRUNCATE TABLE x`` / ``TRUNCATE x``)
  * ``DELETE FROM`` without a ``WHERE`` clause

Every blocked attempt is appended to ``~/.claude/hooks/blocked.log`` with
timestamp, attempted command and project path, and Claude is shown a clear
reason why the command was denied.

Normal commands are passed through untouched.

Hook protocol (Claude Code, PreToolUse):
  * Reads a JSON object on stdin: {"tool_name": "Bash",
    "tool_input": {"command": "..."}, "cwd": "/path/to/project", ...}
  * Only ``Bash`` tool calls are inspected; everything else is allowed.
  * On a block, prints a JSON ``permissionDecision: "deny"`` object to
    stdout and exits 0.
  * On allow, prints a JSON ``permissionDecision: "allow"`` object and
    exits 0.
  * On malformed / missing input, allows (fail-open) — a hook must never
    break Claude Code because of its own parse error.

Stdlib only — no third-party dependencies. Python 3.8+.

Manual check (no Claude Code needed):
    echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /tmp/x"}, "cwd": "/tmp"}' \
      | python3 hooks/block-destructive-commands.py
    python3 hooks/block-destructive-commands.py --check "DELETE FROM users"
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


def get_log_path() -> Path:
    """Log path, overridable for tests via HOOK_BLOCKED_LOG."""
    override = os.environ.get("HOOK_BLOCKED_LOG")
    if override:
        return Path(override)
    return DEFAULT_LOG_PATH


# Words that, as the first word of a shell segment, mean the rest of the
# segment is data being printed/searched, not a command to run. SQL keywords
# inside those segments (e.g. `echo "DROP TABLE users"`) are not blocked.
# rm/git checks still run on the quote-stripped text, so
# `echo "rm -rf /"` is allowed for the right reason: it is only text.
_READONLY_FIRST_WORDS = {"echo", "printf", "grep", "cat", "less", "head", "tail"}

# Leading wrappers that do not change what command is being run.
_WRAPPER_WORDS = {"sudo", "command", "time", "env", "nice", "nohup"}

# Targets that are never safe to `rm -r`, even without -f.
_DANGEROUS_RM_TARGETS = {"/", "~", "*", ".", "..", "$HOME", "/*", "~/*", "./", "../"}


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------

_QUOTED_RE = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`\\]|\\.)*`""")


def strip_quoted_strings(text: str) -> str:
    """Remove single/double-quoted (and backticked) substrings.

    Used for rm/git detection so that e.g. ``echo "rm -rf /"`` is not
    treated as a destructive command — it is only text being printed.
    """
    return _QUOTED_RE.sub("", text)


_SEGMENT_SPLIT_RE = re.compile(r"\s*(?:&&|\|\||;|\||\n)\s*")


def split_shell_segments(command: str) -> list:
    """Split a shell command into segments on &&, ||, ;, | and newlines."""
    return [seg for seg in _SEGMENT_SPLIT_RE.split(command) if seg.strip()]


def first_word(segment: str) -> str:
    """First word of a segment, skipping sudo/env-style wrappers."""
    tokens = segment.strip().split()
    i = 0
    while i < len(tokens) and tokens[i] in _WRAPPER_WORDS:
        i += 1
    # `env FOO=bar <cmd>` — skip VAR=value assignments after env.
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    return tokens[i] if i < len(tokens) else ""


# ---------------------------------------------------------------------------
# Destructive-pattern checks
# Each returns a human-readable reason string, or None if not matched.
# ---------------------------------------------------------------------------

def check_rm(segment_stripped: str) -> str | None:
    """Block `rm` with both recursive and force flags, or recursive rm
    of a dangerous target. `rm file.txt`, `rm -r dir` (no -f) and
    `rm -f file.txt` (no -r) are allowed."""
    tokens = segment_stripped.strip().split()
    # Find the `rm` token, skipping wrappers.
    idx = 0
    while idx < len(tokens) and tokens[idx] in _WRAPPER_WORDS:
        idx += 1
    while idx < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[idx]):
        idx += 1
    if idx >= len(tokens) or tokens[idx] != "rm":
        return None

    flags = set()
    targets = []
    for tok in tokens[idx + 1:]:
        if tok == "--":
            continue
        if tok.startswith("--"):
            flags.add(tok)
        elif tok.startswith("-") and len(tok) > 1 and not tok[1].isdigit():
            # Combined short flags, e.g. -rf, -fr, -r, -f
            for ch in tok[1:]:
                flags.add(f"-{ch}")
        else:
            targets.append(tok)

    recursive = bool(
        {"-r", "-R", "--recursive"} & flags
    )
    force = bool({"-f", "--force"} & flags)

    if recursive and force:
        return "rm with recursive (-r) and force (-f) flags is blocked"
    if recursive and any(t in _DANGEROUS_RM_TARGETS for t in targets):
        return "rm -r targeting a dangerous path (/, ~, *, .) is blocked"
    return None


def check_git_push_force(segment_stripped: str) -> str | None:
    """Block `git push --force` and `git push -f`.

    `--force-with-lease` is deliberately ALLOWED: it is the safe
    alternative to --force, and the bounty only lists --force.
    """
    tokens = segment_stripped.strip().split()
    idx = 0
    while idx < len(tokens) and tokens[idx] in _WRAPPER_WORDS:
        idx += 1
    if len(tokens) - idx < 2 or tokens[idx] != "git" or tokens[idx + 1] != "push":
        return None

    rest = tokens[idx + 2:]
    # Remove the safe variant first so it cannot trigger the --force check
    # (--force-with-lease starts with --force, so check it explicitly).
    has_safe_lease = "--force-with-lease" in rest
    rest_without_lease = [t for t in rest if t != "--force-with-lease"]
    if "--force" in rest_without_lease:
        return "git push --force is blocked (use --force-with-lease instead)"
    if "-f" in rest_without_lease:
        return "git push -f is blocked (use --force-with-lease instead)"
    if has_safe_lease:
        return None
    return None


def check_sql(segment_original: str) -> str | None:
    """Block DROP TABLE, TRUNCATE, and DELETE FROM without WHERE.

    Checked on the original (un-stripped) segment so SQL passed to a
    client — e.g. `psql -c "DROP TABLE users"` — is still caught.
    """
    text = segment_original

    if re.search(r"\bDROP\s+TABLE\b", text, re.IGNORECASE):
        return "DROP TABLE is blocked"
    if re.search(r"\bTRUNCATE\b", text, re.IGNORECASE):
        # TRUNCATE TABLE x / TRUNCATE x — only match when it looks like
        # a SQL statement, not a word inside another identifier.
        if re.search(r"\bTRUNCATE\s+(TABLE\s+)?[\"'`\[]?[A-Za-z_]", text, re.IGNORECASE):
            return "TRUNCATE is blocked"
    # DELETE FROM ... without WHERE: split on ';' (one statement at a time)
    # and block any DELETE statement that has no WHERE before its end.
    for stmt in text.split(";"):
        if re.search(r"\bDELETE\s+FROM\b", stmt, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                return "DELETE FROM without a WHERE clause is blocked"
    return None


def check_command(command: str) -> str | None:
    """Return a block reason for a full (possibly chained) command,
    or None if the command is safe."""
    if not command or not command.strip():
        return None

    for segment in split_shell_segments(command):
        stripped = strip_quoted_strings(segment)
        reason = check_rm(stripped)
        if reason:
            return reason
        reason = check_git_push_force(stripped)
        if reason:
            return reason
        # SQL: skip segments that are only printing/searching text.
        if first_word(stripped) not in _READONLY_FIRST_WORDS:
            reason = check_sql(segment)
            if reason:
                return reason
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_blocked(command: str, cwd: str, reason: str, log_path: Path | None = None) -> None:
    """Append one blocked attempt to blocked.log.

    Format (one line per attempt):
        2026-11-26T12:00:00Z | cwd=/path/to/project | reason=... | command=...
    Failures to write the log are swallowed — logging must never break
    the hook itself.
    """
    path = log_path or get_log_path()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = (
        f"{timestamp} | cwd={cwd or ''} | reason={reason} | "
        f"command={command}\n"
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Hook entry point
# ---------------------------------------------------------------------------

def decide(payload: dict) -> tuple[bool, str | None, str, str]:
    """Decide a PreToolUse payload.

    Returns (allowed, block_reason, command, cwd).
    Non-Bash tools and malformed payloads are allowed (fail-open).
    """
    if not isinstance(payload, dict):
        return True, None, "", ""
    if payload.get("tool_name") not in (None, "Bash"):
        # Only Bash commands are inspected. If tool_name is present and
        # is not Bash, allow immediately.
        if payload.get("tool_name") is not None:
            return True, None, "", payload.get("cwd", "") or ""
    tool_input = payload.get("tool_input") or {}
    if isinstance(tool_input, str):
        command = tool_input
    elif isinstance(tool_input, dict):
        command = tool_input.get("command", "") or ""
    else:
        command = ""
    cwd = payload.get("cwd", "") or ""
    reason = check_command(command)
    if reason:
        return False, reason, command, cwd
    return True, None, command, cwd


def main(argv: list | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Manual check mode: `hook.py --check "rm -rf /tmp/x"`
    if argv and argv[0] == "--check" and len(argv) > 1:
        command = " ".join(argv[1:])
        reason = check_command(command)
        if reason:
            print(f"BLOCKED: {reason}\n  command: {command}")
            return 1
        print(f"ALLOWED: {command}")
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Malformed input: fail open, do not break Claude Code.
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": "Hook could not parse input; allowing.",
            }
        }))
        return 0

    allowed, reason, command, cwd = decide(payload)

    if not allowed:
        log_blocked(command, cwd, reason or "destructive command")
        message = (
            f"Blocked destructive command: {reason}. "
            "This command was not executed. "
            "If you really need this operation, ask the user to run it "
            "manually, or use a safer alternative "
            "(for example, `git push --force-with-lease` instead of "
            "`git push --force`, or `DELETE FROM ... WHERE ...` instead of "
            "a bare `DELETE FROM`)."
        )
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": message,
            }
        }))
        return 0

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Command passed the destructive-command check.",
        }
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
