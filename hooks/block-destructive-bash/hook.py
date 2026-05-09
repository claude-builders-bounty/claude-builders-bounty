#!/usr/bin/env python3
"""Pre-tool-use hook that blocks destructive bash commands in Claude Code.

Reads the PreToolUse JSON event from stdin. If the Bash command matches a
destructive pattern, emits a deny decision and logs the attempt. Otherwise
exits 0 (silent allow).

Run `python hook.py --install` to copy this script into ~/.claude/hooks/
and merge a PreToolUse hook entry into ~/.claude/settings.json.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

CLAUDE_DIR = Path.home() / ".claude"
HOOKS_DIR = CLAUDE_DIR / "hooks"
SETTINGS_PATH = CLAUDE_DIR / "settings.json"
LOG_PATH = HOOKS_DIR / "blocked.log"
INSTALL_NAME = "block_destructive_bash.py"


# ---------------------------------------------------------------------------
# Pattern library
# ---------------------------------------------------------------------------

_SQL_PATTERNS = [
    (
        re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW)\b", re.I),
        "SQL DROP {kind} (irreversible)",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?\w+", re.I),
        "SQL TRUNCATE (bulk irreversible deletion)",
    ),
    (
        # DELETE FROM ... that does not contain WHERE before the next statement
        # terminator. Allows `DELETE FROM t WHERE id=1` but blocks `DELETE FROM t`.
        re.compile(r"\bDELETE\s+FROM\b(?:(?!\bWHERE\b|;).)*(?:;|$)", re.I | re.S),
        "SQL DELETE FROM without WHERE clause (deletes every row)",
    ),
]

_EXTRA_PATTERNS = [
    (
        re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
        "fork bomb",
    ),
    (
        re.compile(r"\bdd\b[^|;&\n]*\bof=/dev/(?:sd|nvme|hd|disk|mmcblk)", re.I),
        "dd writing to a raw block device",
    ),
    (
        re.compile(r"\bmkfs(?:\.\w+)?\s+/dev/(?:sd|nvme|hd)", re.I),
        "mkfs against a raw block device",
    ),
    (
        re.compile(r">\s*/dev/(?:sd|nvme|hd)[a-z]\d*\b"),
        "redirect into a raw block device",
    ),
    (
        re.compile(r"\bchmod\s+-R\s+0?00\b"),
        "recursive chmod 000 (locks the tree out)",
    ),
]

# Fallback regex used only when shlex tokenization fails. Catches the common
# bundled-flag forms (`-rf`, `-fr`, `-Rf`, `-rfv`, …) so a malformed quote in
# the command line cannot smuggle `rm -rf /` past us.
_RM_FALLBACK = re.compile(
    r"\brm\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*[fF]|-[a-zA-Z]*[fF][a-zA-Z]*[rR])\b"
)

# SQL command-line clients whose quoted -c/-e arg IS the SQL payload.
_SQL_CLIS = {
    "psql",
    "mysql",
    "mariadb",
    "mysqldump",
    "sqlite3",
    "duckdb",
    "cockroach",
    "pgcli",
    "mycli",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def strip_line_comments(s: str) -> str:
    """Remove `# …` comments that sit outside quoted strings.

    Best-effort: bash quoting is more nuanced than this, but the goal is just
    to keep `# rm -rf is bad` from tripping the matcher.
    """
    out: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(s):
        c = s[i]
        if quote:
            out.append(c)
            if c == quote and (i == 0 or s[i - 1] != "\\"):
                quote = None
        elif c in ('"', "'"):
            quote = c
            out.append(c)
        elif c == "#":
            while i < len(s) and s[i] != "\n":
                i += 1
            continue
        else:
            out.append(c)
        i += 1
    return "".join(out)


def blank_quoted(s: str) -> str:
    """Replace quoted-string bodies with empty content so regex scans only
    see real shell tokens — `grep 'DROP TABLE' x` becomes `grep '' x`."""
    out: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(s):
        c = s[i]
        if quote:
            if c == quote and s[i - 1] != "\\":
                out.append(c)
                quote = None
            # else: drop the character (it's inside the quoted body)
        elif c in ('"', "'"):
            quote = c
            out.append(c)
        else:
            out.append(c)
        i += 1
    return "".join(out)


def _flag_chars(token: str) -> set[str]:
    """Return the set of single-letter / long flags carried by *token*.

    `-rf`     -> {"r", "f"}
    `--force` -> {"force"}
    `-R`      -> {"R"}
    """
    if token.startswith("--"):
        return {token[2:].lower()}
    if token.startswith("-") and len(token) > 1:
        return set(token[1:])
    return set()


def check_rm_rf(tokens: list[str]) -> str | None:
    """Return a reason if any `rm` invocation has both -r/-R and -f flags."""
    for i, tok in enumerate(tokens):
        if tok != "rm":
            continue
        flags: set[str] = set()
        for t in tokens[i + 1 :]:
            if t == "--":
                break
            if not t.startswith("-"):
                break
            flags |= _flag_chars(t)
        has_r = bool(flags & {"r", "R", "recursive"})
        has_f = bool(flags & {"f", "force"})
        if has_r and has_f:
            return "rm with -r/-R and -f flags (recursive force delete)"
    return None


def check_git_push_force(tokens: list[str]) -> str | None:
    """Block `git push --force` / `-f` but allow `--force-with-lease`."""
    for i, tok in enumerate(tokens):
        if tok != "git":
            continue
        rest = tokens[i + 1 :]
        if not rest or rest[0] != "push":
            continue
        for t in rest[1:]:
            if t == "--force-with-lease" or t.startswith("--force-with-lease="):
                return None  # safer variant — explicitly allowed
            if t == "--force" or t == "-f":
                return "git push --force / -f (use --force-with-lease for safer rewrites)"
            # Bundled short flags such as -fu would still contain "f"
            if t.startswith("-") and not t.startswith("--") and "f" in t[1:]:
                return "git push -f (use --force-with-lease for safer rewrites)"
        return None
    return None


def evaluate(command: str) -> str | None:
    """Return a human-readable block reason, or None to allow the command."""
    if not command or not command.strip():
        return None

    cleaned = strip_line_comments(command)

    # Structural checks via shlex (handles quotes correctly).
    try:
        tokens = shlex.split(cleaned, posix=True)
    except ValueError:
        tokens = []

    if tokens:
        if (reason := check_rm_rf(tokens)):
            return reason
        if (reason := check_git_push_force(tokens)):
            return reason
    elif _RM_FALLBACK.search(cleaned):
        return "rm with -r and -f flags (recursive force delete)"

    # SQL / disk patterns are regex-based. When a SQL CLI is being invoked
    # (`psql -c '...'`, `mysql -e "..."`), keep the quoted bodies — those
    # are the real query payload. Otherwise blank quoted text to avoid
    # tripping on `grep 'DROP TABLE' file.sql`.
    if tokens and any(t in _SQL_CLIS for t in tokens):
        scan = cleaned
    else:
        scan = blank_quoted(cleaned)

    for pat, template in _SQL_PATTERNS:
        m = pat.search(scan)
        if not m:
            continue
        kind = (m.group(1) or "").upper() if m.lastindex else ""
        return template.format(kind=kind)

    for pat, msg in _EXTRA_PATTERNS:
        if pat.search(scan):
            return msg

    return None


def log_block(command: str, reason: str, project: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "reason": reason,
        "project": project,
    }
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Hook entry point
# ---------------------------------------------------------------------------


def run_hook() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Malformed input — fail open. Never block on hook bug.
        return 0

    if event.get("hook_event_name") != "PreToolUse":
        return 0
    if event.get("tool_name") != "Bash":
        return 0

    command = (event.get("tool_input") or {}).get("command", "") or ""
    project = event.get("cwd") or os.getcwd()

    reason = evaluate(command)
    if reason is None:
        return 0

    log_block(command, reason, project)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"Blocked destructive command: {reason}. "
                f"Logged to {LOG_PATH}. Override by editing "
                f"{SETTINGS_PATH} or removing the hook."
            ),
        }
    }
    sys.stdout.write(json.dumps(output))
    return 0


# ---------------------------------------------------------------------------
# Installer
# ---------------------------------------------------------------------------


def install() -> int:
    """Copy this script into ~/.claude/hooks/ and register the hook."""
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    target = HOOKS_DIR / INSTALL_NAME

    src = Path(__file__).resolve()
    if src != target:
        shutil.copy2(src, target)
        target.chmod(0o755)

    settings = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            sys.stderr.write(
                f"error: {SETTINGS_PATH} is not valid JSON ({exc}). "
                "Fix or remove it and re-run --install.\n"
            )
            return 1

    hooks = settings.setdefault("hooks", {})
    pre_tool = hooks.setdefault("PreToolUse", [])

    cmd = f"python {target}"
    already_present = any(
        any(h.get("command") == cmd for h in entry.get("hooks", []))
        for entry in pre_tool
        if isinstance(entry, dict)
    )

    if not already_present:
        pre_tool.append(
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": cmd}],
            }
        )
        SETTINGS_PATH.write_text(
            json.dumps(settings, indent=2) + "\n", encoding="utf-8"
        )
        sys.stdout.write(f"Installed hook -> {target}\n")
        sys.stdout.write(f"Registered PreToolUse entry in {SETTINGS_PATH}\n")
    else:
        sys.stdout.write(
            f"Hook already registered in {SETTINGS_PATH}; refreshed binary at {target}\n"
        )
    return 0


def main(argv: list[str]) -> int:
    if "--install" in argv[1:]:
        return install()
    return run_hook()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
