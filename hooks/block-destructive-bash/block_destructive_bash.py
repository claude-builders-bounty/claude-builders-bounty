#!/usr/bin/env python3
"""
block_destructive_bash.py

Claude Code pre-tool-use hook that intercepts dangerous bash commands before
execution. Blocks a curated set of patterns, logs each blocked attempt to
~/.claude/hooks/blocked.log, and returns a structured decision payload that
Claude Code surfaces back to the model with a clear reason.

Submission for claude-builders-bounty/claude-builders-bounty issue #3.

Hook contract: Claude Code passes a JSON event on stdin. For Bash tool use,
the event includes tool_name == "Bash" and tool_input.command (the shell
string). The hook prints a JSON decision to stdout and exits.

  ALLOW  -> {"decision": "approve"}
  BLOCK  -> {"decision": "block", "reason": "<text shown to model>"}

For events we don't handle (other tools, malformed input), we approve so the
hook never breaks unrelated tool calls.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"


# Each rule is (compiled_regex, human_label, why_it_is_dangerous).
# Patterns are conservative: they block the obvious destructive forms without
# false-positive blocking on safe variants. Tune to taste.
RULES: list[tuple[re.Pattern[str], str, str]] = [
    (
        # rm -rf, rm -fr, rm -r -f, rm --recursive --force, etc.
        # Catches the destructive flag combo regardless of order or long form.
        re.compile(
            r"(?<![A-Za-z0-9_])rm\s+(?:[^|;&\n]*\s)?"
            r"(?:-[A-Za-z]*[rR][A-Za-z]*[fF][A-Za-z]*"
            r"|-[A-Za-z]*[fF][A-Za-z]*[rR][A-Za-z]*"
            r"|--recursive\s+--force"
            r"|--force\s+--recursive)",
        ),
        "rm -rf",
        "Recursive force-delete. Easy to widen with a typo or unset variable "
        "and wipe the wrong tree. Use `trash`/move-to-recycle, or be explicit "
        "about each path with `rm -i`, or run targeted `find ... -delete`.",
    ),
    (
        # DROP TABLE / DROP DATABASE / DROP SCHEMA — anywhere in the command,
        # tolerant of optional IF EXISTS and surrounding whitespace.
        re.compile(
            r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b",
            re.IGNORECASE,
        ),
        "DROP TABLE/DATABASE/SCHEMA",
        "Drops a table, database, or schema. Almost always wrong outside a "
        "migration file. Write it as a forward-only migration instead so the "
        "team can review it.",
    ),
    (
        # git push --force / git push -f / git push --force-with-lease IS allowed
        # because --force-with-lease is the safe variant; we only block the
        # unconditional --force flavors.
        re.compile(
            r"\bgit\s+push\b[^\n]*?(?:--force(?!-with-lease)|(?<!-)\s-f(?!\w))",
        ),
        "git push --force",
        "Unconditional force push overwrites remote history. Use "
        "`--force-with-lease` (which is allowed) so a concurrent collaborator's "
        "work can't be silently clobbered.",
    ),
    (
        # TRUNCATE TABLE / TRUNCATE foo — non-recoverable wipe of all rows.
        re.compile(
            r"\bTRUNCATE\b(?:\s+TABLE)?\s+\w",
            re.IGNORECASE,
        ),
        "TRUNCATE",
        "TRUNCATE empties a table with no row-level audit trail and is not "
        "transactional on every engine. Use `DELETE FROM ... WHERE ...` if "
        "you genuinely mean to remove rows, with the WHERE clause as the "
        "explicit blast-radius declaration.",
    ),
    (
        # DELETE FROM <table> with no WHERE clause anywhere in the statement.
        # We capture the segment from DELETE FROM up to the next semicolon or
        # end-of-string, then require it to NOT contain WHERE. A JSON payload
        # passed via stdin to a CLI is still text — the regex sees it.
        re.compile(
            r"\bDELETE\s+FROM\s+[^\s;]+(?:\s+(?!WHERE\b)[^\s;]+)*\s*(?:;|$)",
            re.IGNORECASE,
        ),
        "DELETE FROM without WHERE",
        "DELETE without a WHERE clause removes every row in the table. If "
        "that is genuinely what you want, use TRUNCATE or write `DELETE "
        "FROM <table> WHERE 1=1` so reviewers see the intent.",
    ),
]


def log_block(command: str, project_path: str | None, rule_label: str) -> None:
    """Append a one-line JSON record to ~/.claude/hooks/blocked.log."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
        "command": command,
        "project_path": project_path,
        "rule": rule_label,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def evaluate(command: str) -> tuple[bool, str | None, str | None]:
    """Return (allowed, rule_label, reason). allowed=False means block."""
    for pattern, label, reason in RULES:
        if pattern.search(command):
            return False, label, reason
    return True, None, None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed event — approve so we never break unrelated tool calls.
        print(json.dumps({"decision": "approve"}))
        return 0

    tool_name = event.get("tool_name") or event.get("tool", {}).get("name")
    if tool_name != "Bash":
        print(json.dumps({"decision": "approve"}))
        return 0

    tool_input = event.get("tool_input") or event.get("tool", {}).get("input") or {}
    command = tool_input.get("command", "")
    if not isinstance(command, str) or not command.strip():
        print(json.dumps({"decision": "approve"}))
        return 0

    allowed, rule_label, reason = evaluate(command)
    if allowed:
        print(json.dumps({"decision": "approve"}))
        return 0

    project_path = (
        event.get("cwd")
        or event.get("project_path")
        or os.environ.get("CLAUDE_PROJECT_DIR")
        or os.getcwd()
    )

    log_block(command=command, project_path=project_path, rule_label=rule_label or "")

    message = (
        f"Blocked by destructive-bash hook (rule: {rule_label}).\n\n"
        f"Why: {reason}\n\n"
        f"This attempt was logged to {LOG_PATH}.\n"
        f"If you genuinely need to run this, do it manually in a terminal, "
        f"or remove the rule from the hook for this session."
    )
    print(json.dumps({"decision": "block", "reason": message}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
