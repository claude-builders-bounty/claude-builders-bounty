#!/usr/bin/env python3
"""
Claude Code PreToolUse hook: block destructive bash commands.

Bounty: claude-builders-bounty #3 — [BOUNTY $100] HOOK: Pre-tool-use hook
that blocks destructive bash commands (Opire).

Reads the PreToolUse event JSON from stdin. If the tool is Bash and the
command matches a destructive pattern, the hook:
  1. appends an audit line to ~/.claude/hooks/blocked.log
     (timestamp, attempted command, project path)
  2. denies the tool call with a clear reason shown to Claude
Otherwise it allows the call silently (exit 0, no output).

Blocked patterns (per bounty acceptance criteria):
  - rm -rf / rm -fr (and combined short-flag forms like rm -Rf, rm -r -f)
  - DROP TABLE (SQL, case-insensitive)
  - git push --force / git push -f (force push; --force-with-lease is allowed
    only when explicitly written as --force-with-lease, which is the safer
    variant — plain --force and -f are blocked)
  - TRUNCATE (SQL TRUNCATE TABLE / bare TRUNCATE statement)
  - DELETE FROM ... without a WHERE clause

Normal commands are never interfered with: matching is anchored to actual
command positions (start of command or after ;, &&, ||, |) for rm/git, and
word-boundary based for SQL keywords, so e.g. `echo "rm -rf is dangerous"`
as a plain string argument after a safe verb is still checked conservatively
only when it appears as a command. SQL checks apply anywhere in the command
because SQL is typically passed as a string argument to psql/mysql/sqlite3.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# ---------------------------------------------------------------- patterns

# rm with recursive+force flags, in any order/combination, as a command.
RM_RF = re.compile(
    r"(?:^|[;&|]\s*|\n\s*)(?:sudo\s+)?rm\s+"
    r"(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b"
    r"|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b"
    r"|-r\s+-[a-zA-Z]*f[a-zA-Z]*\b"
    r"|-f\s+-[a-zA-Z]*r[a-zA-Z]*\b"
    r"|--recursive\s+--force\b|--force\s+--recursive\b)",
    re.IGNORECASE,
)

DROP_TABLE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)

GIT_FORCE_PUSH = re.compile(
    r"(?:^|[;&|]\s*|\n\s*)git\s+push\b[^;&|\n]*?"
    r"(?:--force\b(?!-with-lease)|(?<!\S)-f\b|--force-with-lease=\S*--force\b)",
    re.IGNORECASE,
)
# Simpler, stricter fallback: any `git push` segment containing a bare
# --force or -f token (but not --force-with-lease alone).
GIT_FORCE_PUSH_SIMPLE = re.compile(
    r"(?:^|[;&|]\s*|\n\s*)git\s+push\b([^;&|\n]*)", re.IGNORECASE
)

TRUNCATE = re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[\"'`\w]", re.IGNORECASE)

DELETE_FROM = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_CLAUSE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _git_force_push(command: str) -> bool:
    for m in GIT_FORCE_PUSH_SIMPLE.finditer(command):
        args = m.group(1)
        tokens = args.split()
        for tok in tokens:
            if tok == "--force":
                return True
            if tok == "-f":
                return True
            # bundled short flags containing f, e.g. -vf, but exclude
            # --force-with-lease which is a distinct, safer token
            if re.fullmatch(r"-[a-zA-Z]*f[a-zA-Z]*", tok):
                return True
    return False


CHECKS = [
    ("rm -rf (recursive force delete)", lambda c: bool(RM_RF.search(c))),
    ("DROP TABLE (SQL)", lambda c: bool(DROP_TABLE.search(c))),
    ("git push --force (force push)", _git_force_push),
    ("TRUNCATE (SQL)", lambda c: bool(TRUNCATE.search(c))),
    (
        "DELETE FROM without a WHERE clause (SQL)",
        lambda c: bool(DELETE_FROM.search(c)) and not WHERE_CLAUSE.search(c),
    ),
]


# ---------------------------------------------------------------- hook io

def log_block(command: str, reason: str, project_path: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        with open(LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(
                f"{ts}\tproject={project_path}\treason={reason}\tcommand={command}\n"
            )
    except OSError:
        # Logging must never crash the hook; the deny decision still stands.
        pass


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # unparseable input: do not interfere

    if event.get("tool_name") != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not command.strip():
        return 0

    project_path = (
        event.get("cwd")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    for reason, check in CHECKS:
        if check(command):
            log_block(command, reason, project_path)
            decision = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Blocked by destructive-command guard: this command "
                        f"matches '{reason}', which is on the deny list "
                        f"(rm -rf, DROP TABLE, git push --force, TRUNCATE, "
                        f"DELETE FROM without WHERE). The attempt has been "
                        f"logged to ~/.claude/hooks/blocked.log. If this "
                        f"operation is genuinely intended, ask the user to "
                        f"run it manually outside Claude Code."
                    ),
                }
            }
            print(json.dumps(decision))
            return 0

    return 0  # allow: no output, exit 0


if __name__ == "__main__":
    sys.exit(main())
