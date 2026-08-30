#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code — blocks destructive bash commands.

Installed at ~/.claude/hooks/pre_tool_use_blocker.py
Configured via ~/.claude/settings.json  (see README)

Blocked patterns:
  - rm -rf / rm -fr / rm --recursive --force
  - DROP TABLE / DROP DATABASE (SQL)
  - git push --force / -f
  - TRUNCATE [TABLE]
  - DELETE FROM ... without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log
Prints a clear reason so Claude understands and corrects course.
"""
import json
import os
import re
import sys
import datetime

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOKS_DIR, "blocked.log")

# Compiled patterns -> human reason. Ordered, first match wins.
RULES = [
    # rm -rf variants (any depth of -r/-f flags)
    (re.compile(r"\brm\s+.*(?:\-r.*\-f|\-f.*\-r|--recursive|--force)"),
     "DESTRUCTIVE: 'rm' with recursive/force flags can delete irrecoverable data. Refactor to use a trash dir or `rm` without -rf, and confirm the exact path."),
    # SQL destructive / data-loss statements
    (re.compile(r"\bDROP\s+TABLE\b", re.I),
     "DESTRUCTIVE SQL: 'DROP TABLE' permanently removes schema + data. Create a migration that renames/archives the table instead."),
    (re.compile(r"\bDROP\s+DATABASE\b", re.I),
     "DESTRUCTIVE SQL: 'DROP DATABASE' removes an entire database. Abort — use a migration and DB snapshot instead."),
    (re.compile(r"\bTRUNCATE\b", re.I),
     "DESTRUCTIVE SQL: 'TRUNCATE' deletes all rows in a table irrecoverably. Prefer a scoped DELETE with a WHERE clause + backup."),
    # DELETE FROM ... WITHOUT a WHERE clause (naive token check, one statement)
    (re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_\"`\[\].]+\s*(?:;|\Z)", re.I),
     "DESTRUCTIVE SQL: 'DELETE FROM' without a WHERE clause wipes the whole table. Add a WHERE predicate to scope the delete."),
    # git push --force / -f
    (re.compile(r"\bgit\s+push\b.*(?:\-f\b|--force\b)"),
     "DESTRUCTIVE GIT: 'git push --force' rewrites remote history and can lose others' work. Use '--force-with-lease' or open a PR instead."),
]


def is_blocked(command: str):
    for pattern, reason in RULES:
        m = pattern.search(command)
        if m:
            return reason
    return None


def log_block(command: str, reason: str):
    try:
        os.makedirs(HOOKS_DIR, exist_ok=True)
        ts = datetime.datetime.utcnow().isoformat() + "Z"
        # project path: nearest ancestor with a git dir, else cwd
        cwd = os.getcwd()
        project = cwd
        cur = cwd
        while cur and cur != os.path.dirname(cur):
            if os.path.isdir(os.path.join(cur, ".git")):
                project = cur
                break
            cur = os.path.dirname(cur)
        line = json.dumps(
            {"timestamp": ts, "command": command, "reason": reason, "project": project}
        )
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        # never crash the tool because logging failed
        pass


def main():
    # Claude Code hooks pass JSON payload on stdin: {"tool_name":"Bash","tool_input":{"command":"..."}}
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input", {}) or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""

    # Only gate the Bash/Shell tool with a command string.
    if tool != "Bash" or not isinstance(command, str) or not command.strip():
        # not a bash command we gate -> allow (exit 0)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
        return 0

    stripped = re.sub(r"\s{2,}", " ", command.strip())
    reason = is_blocked(stripped)
    if reason:
        log_block(stripped, reason)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "block",
                "reason": reason,
            }
        }
        print(json.dumps(output))
        return 1

    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "allow"}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
