#!/usr/bin/env python3
"""
safe-bash — Claude Code pre-tool-use hook.

Blocks dangerous shell commands before they are executed. Reads the
hook event payload as JSON from stdin (per the Claude Code hooks spec),
inspects any `command` field on Bash tool invocations, and refuses to
allow patterns matching the block list.

Patterns blocked (case-insensitive where appropriate):

  - rm -rf  (and variants: -r -f, -fr, -rfv, -Rf, etc.)
  - DROP TABLE
  - git push --force / git push -f
  - TRUNCATE TABLE
  - DELETE FROM <table>  without a WHERE clause

Every blocked attempt is appended to ~/.claude/hooks/blocked.log with the
timestamp, attempted command, and cwd of the calling project.

Exit codes (per Claude Code hooks spec):
  0 -- allow the tool call
  2 -- block the tool call; stderr is shown to Claude as the reason

The hook also emits a JSON object on stdout in the documented shape:

  {"decision": "block", "reason": "<human-readable explanation>"}

so that newer Claude Code versions that consume structured hook output
get the same result without parsing stderr.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


LOG_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = LOG_DIR / "blocked.log"


# Each entry: (compiled regex, human-readable name, suggestion shown to Claude).
BLOCK_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        # rm -rf in all flag orderings: -rf, -fr, -Rf, -r -f, -rfv, --recursive --force, etc.
        re.compile(
            r"""(?ix)
            \brm \s+
            (?:
                # Single combined flag containing both r and f
                -[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*
              | -[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*
                # Or separate -r / --recursive / -R AND -f / --force flags (in any order)
              | (?:-r\b|--recursive\b|-R\b) \s+ (?:[^\n;|&]*\s+)? (?:-f\b|--force\b)
              | (?:-f\b|--force\b)         \s+ (?:[^\n;|&]*\s+)? (?:-r\b|--recursive\b|-R\b)
            )
            """
        ),
        "rm -rf",
        "Use `rm -ri` for interactive removal, or remove specific paths explicitly. "
        "If you really mean to recursively force-delete, ask the user to run the command themselves.",
    ),
    (
        re.compile(r"(?i)\bDROP\s+TABLE\b"),
        "DROP TABLE",
        "Schema-level destructive SQL. Ask the user to run this manually if it is intentional, "
        "and confirm there is a backup.",
    ),
    (
        # git push followed (on the same logical line) by --force / -f / +<ref>
        re.compile(
            r"""(?x)
            \bgit \s+ push \b
            (?:[^\n;|&]*?)
            (?:
                --force\b (?!-with-lease)        # bare --force, but not --force-with-lease
              | \s -f\b (?!\w)                   # -f as its own short flag
              | \s \+ [\w\-./]+                  # refspec form: git push origin +main
            )
            """
        ),
        "git push --force",
        "Force-push can overwrite teammates' work. Use `--force-with-lease` if you must, "
        "and confirm with the user that the remote branch is safe to rewrite.",
    ),
    (
        re.compile(r"(?i)\bTRUNCATE\s+TABLE\b"),
        "TRUNCATE TABLE",
        "Truncate empties an entire table irreversibly. Ask the user to run this manually if intentional.",
    ),
]


# DELETE FROM <table>  without a WHERE clause is checked per-statement so
# that the WHERE may appear anywhere later in the statement.
DELETE_FROM_RE = re.compile(r"(?i)\bDELETE\s+FROM\s+[\w.\"`\[\]]+\b")
WHERE_RE = re.compile(r"(?i)\bWHERE\b")


def split_statements(cmd: str) -> list[str]:
    """Split a shell command into SQL-ish statements on `;` while keeping bash command separators usable.

    We're only interested in segments that look like SQL invocations, so the
    coarse split-on-semicolon is fine — bash `;` chains will be checked
    statement-by-statement and the regexes ignore whitespace anyway.
    """
    return [s for s in cmd.split(";") if s.strip()]


def check_delete_without_where(cmd: str) -> bool:
    """Return True if any DELETE FROM statement lacks a WHERE clause."""
    for stmt in split_statements(cmd):
        if DELETE_FROM_RE.search(stmt) and not WHERE_RE.search(stmt):
            return True
    return False


def find_block_reason(cmd: str) -> tuple[str, str] | None:
    """Return (pattern_name, suggestion) if `cmd` matches any block rule, else None."""
    for regex, name, suggestion in BLOCK_PATTERNS:
        if regex.search(cmd):
            return name, suggestion
    if check_delete_without_where(cmd):
        return (
            "DELETE FROM ... (no WHERE clause)",
            "A DELETE without WHERE removes every row. Add a WHERE clause, or run the statement manually if "
            "you really intend to clear the table.",
        )
    return None


def log_blocked(cmd: str, pattern_name: str, project_path: str) -> None:
    """Append a single-line record of the blocked attempt to ~/.claude/hooks/blocked.log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    # Quote the command so log lines are easy to grep and don't get split by embedded newlines.
    safe_cmd = cmd.replace("\n", "\\n").replace("\r", "\\r")
    line = f"{timestamp}\t{pattern_name}\t{project_path}\t{safe_cmd}\n"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        # If logging fails (read-only home, full disk, etc.) we still want to
        # block the command — never swallow the policy decision for a logging
        # problem.
        pass


def extract_bash_command(payload: dict) -> str | None:
    """Pull the bash command string out of the hook payload, regardless of which
    schema version Claude Code is using."""
    tool_name = payload.get("tool_name") or payload.get("tool") or ""
    if tool_name.lower() != "bash":
        return None

    # New-style payload: {"tool_input": {"command": "..."}}
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        cmd = tool_input.get("command")
        if isinstance(cmd, str) and cmd.strip():
            return cmd

    # Older payloads sometimes flatten the command up to the top level.
    cmd = payload.get("command")
    if isinstance(cmd, str) and cmd.strip():
        return cmd

    return None


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        # No payload (e.g. running outside Claude Code) -- allow silently.
        return 0

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed payload -- be permissive rather than block legitimate calls.
        print(json.dumps({"decision": "allow"}))
        return 0

    cmd = extract_bash_command(payload)
    if cmd is None:
        # Not a Bash invocation, or no command string -- allow.
        print(json.dumps({"decision": "allow"}))
        return 0

    match = find_block_reason(cmd)
    if match is None:
        print(json.dumps({"decision": "allow"}))
        return 0

    pattern_name, suggestion = match
    project_path = payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_blocked(cmd, pattern_name, project_path)

    reason = (
        f"Destructive command blocked by safe-bash hook: '{pattern_name}'. "
        f"{suggestion} "
        f"(logged to {LOG_FILE})"
    )

    # Structured output for newer Claude Code versions.
    print(json.dumps({"decision": "block", "reason": reason}))
    # Stderr is shown to Claude on exit code 2 in older versions.
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
