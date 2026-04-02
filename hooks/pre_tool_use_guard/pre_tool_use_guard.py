#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Guard Hook
Blocks destructive bash commands before they execute.

Location: ~/.claude/hooks/pre_tool_use_guard.py
Logs all blocked attempts to: ~/.claude/hooks/blocked.log
"""

import json
import sys
import os
import re
from datetime import datetime, timezone


# ── Log file location ──────────────────────────────────────────────────────────
HOOK_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(HOOK_DIR, "blocked.log")


# ── Severity levels ────────────────────────────────────────────────────────────
CRITICAL = "CRITICAL"
HIGH     = "HIGH"
MEDIUM   = "MEDIUM"


# ── Destructive patterns ───────────────────────────────────────────────────────
DESTRUCTIVE_PATTERNS = [
    {
        "name": "curl/wget pipe to shell (remote code execution)",
        "severity": CRITICAL,
        "pattern": re.compile(
            r"(?:curl|wget)\b[^\|;&\n]*\|\s*(?:ba)?sh\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: piping a remote script directly into a shell is a "
            "classic supply-chain attack vector — the remote content could execute anything "
            "with your privileges. Never run untrusted URLs this way.\n"
            "Safe alternatives:\n"
            "  • Download first, inspect, then run:\n"
            "    `curl -fsSL <url> -o install.sh && less install.sh && bash install.sh`\n"
            "  • Use a package manager (apt, brew, pip) whenever possible."
        ),
    },
    {
        "name": "fork bomb",
        "severity": CRITICAL,
        "pattern": re.compile(
            r":\(\)\s*\{.*:\s*\|.*:.*&.*\}",
            re.IGNORECASE | re.DOTALL,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: fork bomb detected. This will spawn processes "
            "exponentially until the system runs out of resources and becomes unresponsive. "
            "Run this only in an isolated VM or container — never on your host."
        ),
    },
    {
        "name": "mkfs (format filesystem)",
        "severity": CRITICAL,
        "pattern": re.compile(
            r"\bmkfs\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: `mkfs` formats a device, destroying all existing data. "
            "This is irreversible without a full backup.\n"
            "  • Verify the target device with `lsblk` before proceeding.\n"
            "  • Run manually after confirming the correct device path."
        ),
    },
    {
        "name": "dd to raw disk device",
        "severity": CRITICAL,
        "pattern": re.compile(
            r"\bdd\b[^\n]*of=/dev/(?!null|zero|urandom|random)[^\s]+",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: `dd` writing directly to a raw disk device will "
            "overwrite data with no recovery path.\n"
            "  • Double-check `of=` target with `lsblk` / `fdisk -l`.\n"
            "  • Run manually after confirming the correct device and size."
        ),
    },
    {
        "name": "rm -rf (recursive force delete)",
        "severity": CRITICAL,
        "pattern": re.compile(
            r"\brm\s+(?:[^\|;&\n]*\s)?-[^\s]*f[^\s]*r[^\s]*\s|"
            r"\brm\s+(?:[^\|;&\n]*\s)?-[^\s]*r[^\s]*f[^\s]*\s|"
            r"\brm\s+-rf\b|\brm\s+-fr\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: `rm -rf` permanently removes files and directories "
            "with no confirmation. This is irreversible.\n"
            "Safe alternatives:\n"
            "  • `rm -i` — interactive, asks before each deletion\n"
            "  • `trash` / `gio trash` — moves to trash (recoverable)\n"
            "  • `rm -r` without `-f` — prompts on protected files"
        ),
    },
    {
        "name": "SQL DROP DATABASE",
        "severity": CRITICAL,
        "pattern": re.compile(
            r"\bDROP\s+DATABASE\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [CRITICAL] Blocked: `DROP DATABASE` destroys an entire database — every "
            "table, index, and row it contains. Irreversible without a backup.\n"
            "  • Back up first: `pg_dump`, `mysqldump`, etc.\n"
            "  • Verify you're connected to the correct server and database name.\n"
            "  • Run manually after confirming the impact."
        ),
    },
    {
        "name": "git push --force",
        "severity": HIGH,
        "pattern": re.compile(
            r"\bgit\s+push\b(?:[^\|;&\n]*\s)--force\b|"
            r"\bgit\s+push\b(?:[^\|;&\n]*\s)-f\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [HIGH] Blocked: `git push --force` rewrites remote history and can "
            "permanently destroy teammates' commits.\n"
            "Safe alternatives:\n"
            "  • `git push --force-with-lease` — fails if remote has unseen commits\n"
            "  • `git push --force-if-includes` — even safer (Git 2.30+)\n"
            "  • Run manually after reviewing the diff."
        ),
    },
    {
        "name": "SQL DROP TABLE",
        "severity": HIGH,
        "pattern": re.compile(
            r"\bDROP\s+TABLE\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [HIGH] Blocked: `DROP TABLE` permanently deletes a table and all its data.\n"
            "  • Back up first: `pg_dump`, `mysqldump`, etc.\n"
            "  • Use `DROP TABLE IF EXISTS` inside a transaction so you can ROLLBACK.\n"
            "  • Run manually after reviewing the impact."
        ),
    },
    {
        "name": "SQL TRUNCATE",
        "severity": HIGH,
        "pattern": re.compile(
            r"\bTRUNCATE\b(?:\s+TABLE)?\s+\w",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [HIGH] Blocked: `TRUNCATE` deletes ALL rows from a table instantly and "
            "cannot be rolled back in most databases.\n"
            "  • Back up the data first.\n"
            "  • Consider `DELETE FROM <table> WHERE <condition>` for surgical removals.\n"
            "  • Run manually in a controlled environment."
        ),
    },
    {
        "name": "SQL DELETE without WHERE",
        "severity": HIGH,
        "pattern": re.compile(
            r"\bDELETE\s+FROM\s+\w+\s*(?:;|$|\bLIMIT\b|\bRETURNING\b|\bUSING\b)",
            re.IGNORECASE | re.MULTILINE,
        ),
        "message": (
            "⛔  [HIGH] Blocked: `DELETE FROM <table>` without a WHERE clause erases "
            "every row. Almost always a mistake.\n"
            "  • Add a WHERE clause to target only the intended rows.\n"
            "  • Preview with: `BEGIN; DELETE ...; SELECT COUNT(*); ROLLBACK;`\n"
            "  • Run manually after double-checking the scope."
        ),
    },
    {
        "name": "chmod -R 777 (world-writable recursive)",
        "severity": HIGH,
        "pattern": re.compile(
            r"\bchmod\s+(?:[^\|;&\n]*\s)?-[^\s]*R[^\s]*\s+(?:777|a\+rwx)\b|"
            r"\bchmod\s+(?:777|a\+rwx)\s+(?:[^\|;&\n]*\s)?-[^\s]*R\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [HIGH] Blocked: `chmod -R 777` makes files world-readable, "
            "world-writable, and world-executable — a serious security vulnerability.\n"
            "  • Use the minimum permissions needed (e.g. 755 for dirs, 644 for files).\n"
            "  • Run manually and only on the specific paths you've verified."
        ),
    },
    {
        "name": "git reset --hard",
        "severity": MEDIUM,
        "pattern": re.compile(
            r"\bgit\s+reset\b(?:[^\|;&\n]*\s)?--hard\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [MEDIUM] Blocked: `git reset --hard` permanently discards all uncommitted "
            "changes. Any unsaved work will be gone.\n"
            "Safe alternatives:\n"
            "  • `git stash` — saves changes so you can restore them later\n"
            "  • `git reset --soft HEAD~1` — undoes the last commit but keeps changes staged\n"
            "  • `git restore .` — discards working tree changes file-by-file"
        ),
    },
    {
        "name": "git clean -fd (force-delete untracked files)",
        "severity": MEDIUM,
        "pattern": re.compile(
            r"\bgit\s+clean\b(?:[^\|;&\n]*\s)-[^\s]*f[^\s]*d[^\s]*\b|"
            r"\bgit\s+clean\b(?:[^\|;&\n]*\s)-[^\s]*d[^\s]*f[^\s]*\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [MEDIUM] Blocked: `git clean -fd` permanently deletes all untracked "
            "files and directories, including new uncommitted work.\n"
            "  • `git clean -n` — dry-run: shows what WOULD be deleted\n"
            "  • `git stash -u` — stashes untracked files (recoverable)\n"
            "  • Review `git status` first and delete specific files manually."
        ),
    },
    {
        "name": "kill -9 -1 (kill all user processes)",
        "severity": MEDIUM,
        "pattern": re.compile(
            r"\bkill\s+(?:[^\|;&\n]*\s)?-9\s+-1\b|"
            r"\bkill\s+(?:[^\|;&\n]*\s)?-KILL\s+-1\b|"
            r"\bkillall\s+(?:[^\|;&\n]*\s)?-9\b",
            re.IGNORECASE,
        ),
        "message": (
            "⛔  [MEDIUM] Blocked: `kill -9 -1` sends SIGKILL to every process owned by "
            "you, including your shell and editor. This will terminate your session.\n"
            "  • Use `kill <pid>` to target a specific process.\n"
            "  • Use `pkill <name>` or `killall <name>` to target by process name."
        ),
    },
]


def _ensure_log_dir() -> None:
    os.makedirs(HOOK_DIR, exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("# Claude Code Blocked Commands Log\n")
            f.write("# Format: ISO timestamp | severity | pattern matched | project path | command\n\n")


def _log_blocked(pattern_name: str, severity: str, command: str) -> None:
    _ensure_log_dir()
    timestamp = datetime.now(timezone.utc).isoformat()
    project_path = os.getcwd()
    safe_command = command.replace("\n", " ↵ ").replace("\r", "")
    entry = f"{timestamp} | {severity} | {pattern_name} | {project_path} | {safe_command}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except OSError:
        pass  # never block on log failure


def _check_command(command: str):
    for rule in DESTRUCTIVE_PATTERNS:
        if rule["pattern"].search(command):
            return True, rule["message"], rule["name"], rule["severity"]
    return False, "", "", ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"[security-guard] WARNING: could not parse hook payload: {e}\n")
        sys.exit(0)

    tool_name: str = payload.get("tool_name", "")
    tool_input: dict = payload.get("tool_input", {})

    if tool_name not in ("Bash", "bash", "shell", "run_bash_command"):
        sys.exit(0)

    command: str = tool_input.get("command", "") or tool_input.get("cmd", "")
    if not command:
        sys.exit(0)

    blocked, message, pattern_name, severity = _check_command(command)

    if blocked:
        _log_blocked(pattern_name, severity, command)
        print(message, flush=True)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
