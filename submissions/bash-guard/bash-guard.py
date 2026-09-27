#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: block destructive bash commands.

Blocks:
  - rm -rf (and other recursive+forced removals)
  - DROP TABLE / DROP DATABASE / DROP SCHEMA
  - git push --force / -f / --force-with-lease
  - TRUNCATE TABLE
  - DELETE FROM without a WHERE clause

Logs every blocked attempt to ~/.claude/hooks/blocked.log
Reads the hook payload from stdin as JSON (Claude Code hooks format).
Exit code 2 => block the tool call and show stderr to Claude.
Exit code 0 => allow.
"""
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# --- SQL rules run on the *whole* command (SQL is often inside -c "..." ) ----
SQL_RULES = [
    (
        "DROP TABLE",
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "`DROP TABLE`/`DROP DATABASE` destroys data and schema permanently",
    ),
    (
        "TRUNCATE",
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?\w", re.IGNORECASE),
        "`TRUNCATE` removes all rows from a table with no undo",
    ),
    (
        "DELETE without WHERE",
        re.compile(
            r"\bDELETE\s+FROM\s+[\w.\"`\[\]]+\s*(?:;|['\"]|$)",
            re.IGNORECASE,
        ),
        "`DELETE FROM <table>` with no `WHERE` clause deletes every row",
    ),
]

# --- Shell rules run per-token on the parsed command -------------------------
def shell_violations(argv):
    """argv is the shlex-split command (best effort)."""
    hits = []
    # rm -rf : a real rm invocation whose flags include both r and f
    for i, tok in enumerate(argv):
        base = os.path.basename(tok)
        if base == "rm":
            flags = []
            for nxt in argv[i + 1:]:
                if nxt.startswith("-") and not nxt.startswith("--"):
                    flags.extend(nxt[1:])
                elif nxt.startswith("--"):
                    flags.append(nxt[2:])
                else:
                    break
            joined = "".join(flags)
            has_r = ("r" in joined) or ("R" in joined) or ("recursive" in flags)
            has_f = ("f" in joined) or ("force" in flags)
            if has_r and has_f:
                hits.append(("rm -rf", "recursive + forced deletion (`rm -rf`) can wipe directories irreversibly"))
    return hits


def git_violations(command: str):
    hits = []
    rx = re.compile(r"\bgit\s+push\b[^\n;&|]*(?:--force(?:-with-lease|-if-includes)?\b|(?<![\w-])-f(?![\w-]))")
    if rx.search(command):
        hits.append(("git push --force", "`git push --force` rewrites remote history and can destroy teammates' work"))
    return hits


def find_violations(command: str):
    hits = []
    hits.extend(shell_violations(_safe_split(command)))
    hits.extend(git_violations(command))
    for name, rx, why in SQL_RULES:
        if rx.search(command):
            hits.append((name, why))
    # de-dupe by rule name, keep order
    seen, out = set(), []
    for h in hits:
        if h[0] not in seen:
            seen.add(h[0])
            out.append(h)
    return out


def _safe_split(command: str):
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        # unbalanced quotes etc. -> fall back to whitespace split
        return command.split()


def log_block(command: str, rules, project_path: str):
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "command": command,
            "project_path": project_path,
            "rules": [r[0] for r in rules],
        }
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # never fail the hook because logging failed


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}

    tool_input = payload.get("tool_input") or {}
    command = (
        tool_input.get("command")
        or payload.get("command")
        or tool_input.get("cmd")
        or ""
    )
    project_path = payload.get("cwd") or os.getcwd()

    if not command.strip():
        return 0

    violations = find_violations(command)
    if not violations:
        return 0

    log_block(command, violations, project_path)

    reason = "Blocked destructive command(s): " + "; ".join(
        f"{name} ({why})" for name, why in violations
    )
    # Canonical Claude Code hook decision (docs: hooks reference, PreToolUse).
    decision = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(decision))

    # Also print a human-readable note to stderr and exit 2, so the hook works
    # under both the JSON-decision and the legacy exit-code convention.
    lines = ["🛑 Blocked by bash-guard pre-tool-use hook:"]
    for name, why in violations:
        lines.append(f"  • {name}: {why}")
    lines += ["", f"Command: {command.strip()}", "",
              "If this is truly intended, ask the user to run it manually."]
    sys.stderr.write("\n".join(lines) + "\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
