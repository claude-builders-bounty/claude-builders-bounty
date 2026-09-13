#!/usr/bin/env python3
"""Claude Code PreToolUse hook: block destructive bash commands.

Reads hook input JSON from stdin (Claude Code format):
  {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "/path", ...}

Exit codes (Claude Code convention):
  0 -> allow command
  2 -> block command (message on stderr is shown to Claude)

Blocked patterns:
  - rm -rf / rm -fr (with root-ish or recursive force targets)
  - DROP TABLE, TRUNCATE (SQL destructive)
  - git push --force / -f
  - DELETE FROM without WHERE clause

Every blocked attempt is appended to ~/.claude/hooks/blocked.log as:
  ISO8601-timestamp | cwd=<project path> | command=<attempted command> | rule=<rule id>
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_log_path() -> Path:
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def detect_violation(command: str):
    """Return (rule_id, reason) if command is destructive, else (None, None)."""
    if not command or not command.strip():
        return None, None
    cmd = command.strip()

    # 1. rm -rf / -fr : recursive force remove. Block any use to be safe,
    #    except a fully commented-out line.
    if not cmd.lstrip().startswith("#"):
        if re.search(r"\brm\s+(?=[^\n]*-[a-zA-Z]*r)(?=[^\n]*-[a-zA-Z]*f)[^\n]*", cmd) or \
           re.search(r"\brm\s+(?=[^\n]*-[a-zA-Z]*f)(?=[^\n]*-[a-zA-Z]*r)[^\n]*", cmd):
            return ("rm-rf",
                    "Blocked 'rm -rf': recursive force deletion is irreversible "
                    "and can wipe a project or home directory with one typo.")

    lowered = cmd.lower()

    # Read-only inspection commands (grep/rg/echo/...) that merely MENTION a
    # destructive keyword must not be blocked - unless they pipe into a real
    # SQL client or shell that would execute it.
    inspection_only = re.match(
        r"\s*(grep|rg|ag|ack|echo|printf|cat|less|head|tail)\b", lowered
    ) and not re.search(
        r"\b(psql|mysql|mariadb|sqlite3|sqlcmd|psql\.exe)\b", lowered
    )

    # 2. SQL: DROP TABLE
    if not inspection_only and re.search(r"\bdrop\s+table\b", lowered):
        return ("drop-table",
                "Blocked 'DROP TABLE': dropping a table destroys all its data. "
                "Use a migration with backup/review instead.")

    # 3. SQL: TRUNCATE [TABLE]
    if not inspection_only and re.search(r"\btruncate\b(\s+table)?\s+\S+", lowered):
        return ("truncate",
                "Blocked 'TRUNCATE': it deletes all rows without logging "
                "individual row deletions. Use a reviewed migration instead.")

    # 4. git push --force / -f (but allow --force-with-lease, the safe variant)
    if re.search(r"\bgit\s+push\b", lowered):
        if re.search(r"--force(?!\s*=\s*|\s*-with-lease)|--force\b(?!\s*-with-lease)", cmd) or \
           re.search(r"\bgit\s+push\b[^\n|;&]*\s-f(\s|$)", cmd):
            if "--force-with-lease" not in cmd:
                return ("git-force-push",
                        "Blocked 'git push --force': it rewrites shared history "
                        "and can permanently lose teammates' work. "
                        "Use 'git push --force-with-lease' after review instead.")

    # 5. DELETE FROM without WHERE (across the whole statement)
    if inspection_only:
        return None, None
    for m in re.finditer(r"\bdelete\s+from\s+\S+", lowered):
        tail = lowered[m.end():]
        # cut at statement terminator
        tail = tail.split(";")[0]
        if not re.search(r"\bwhere\b", tail):
            return ("delete-without-where",
                    "Blocked 'DELETE FROM' without WHERE: it would delete every "
                    "row in the table. Add a WHERE clause or use TRUNCATE "
                    "intentionally via migration.")

    return None, None


def log_blocked(command: str, project_path: str, rule_id: str) -> None:
    try:
        log_path = get_log_path()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).isoformat()
        line = f"{ts} | cwd={project_path} | rule={rule_id} | command={command}\n"
        with log_path.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass  # logging must never break the hook


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        data = {}

    tool_input = data.get("tool_input", {}) if isinstance(data, dict) else {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    project_path = (
        data.get("cwd") or data.get("project_path")
        or tool_input.get("cwd", "") or os.getcwd()
    )

    rule_id, reason = detect_violation(command)
    if rule_id:
        log_blocked(command, project_path, rule_id)
        message = f"BLOCKED [{rule_id}]: {reason}\nAttempted: {command}"
        # Human-readable for Claude (stderr) + structured JSON (stdout)
        print(message, file=sys.stderr)
        print(json.dumps({"decision": "block", "reason": message}))
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
