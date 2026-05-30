#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: block dangerous bash commands.

This hook is intended to be installed at: ~/.claude/hooks/block-dangerous-bash.py
and referenced from your Claude Code settings hooks config.

It blocks:
- rm -rf
- git push --force (and -f)
- DROP TABLE
- TRUNCATE
- DELETE FROM without a WHERE clause

On block, it logs to ~/.claude/hooks/blocked.log with:
timestamp, attempted command, project path.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import shlex
from pathlib import Path


GIT_PUSH_FORCE_RE = re.compile(r"(^|\s)git\s+push(\s|$).*?(\s(--force|-f)(\s|$))")
DROP_TABLE_RE = re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE)
TRUNCATE_RE = re.compile(r"\bTRUNCATE\b", re.IGNORECASE)
DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE)
WHERE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _project_path(payload: dict) -> str:
    # Claude Code commonly provides cwd/project path in payload; fall back to env.
    for key in ("cwd", "projectPath", "project_path", "workspace", "repoRoot"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return os.getcwd()


def _blocked_log_path() -> Path:
    hooks_dir = Path.home() / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    return hooks_dir / "blocked.log"


def _rm_has_r_and_f(cmd: str) -> bool:
    """Return True if cmd looks like an rm invocation with both recursive and force.

    This catches: rm -rf, rm -fr, rm -r -f, rm -f -r, rm --recursive --force, etc.
    """
    try:
        parts = shlex.split(cmd, posix=True)
    except Exception:
        parts = cmd.split()
    if not parts or parts[0] != "rm":
        return False

    has_r = False
    has_f = False
    for tok in parts[1:]:
        if tok == "--":
            break
        if tok.startswith("--"):
            if tok == "--recursive":
                has_r = True
            elif tok == "--force":
                has_f = True
            continue
        if tok.startswith("-") and len(tok) > 1:
            flags = tok[1:]
            if "r" in flags:
                has_r = True
            if "f" in flags:
                has_f = True
        else:
            # First non-flag argument => stop scanning options.
            break
    return has_r and has_f


def _sanitize_field(value: str) -> str:
    # Prevent log injection into a tab-separated log by normalizing control chars.
    return value.replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def _classify(cmd: str) -> str | None:
    c = cmd.strip()
    if not c:
        return None

    if _rm_has_r_and_f(c):
        return "Blocked destructive delete: rm -rf"
    if GIT_PUSH_FORCE_RE.search(c):
        return "Blocked dangerous git operation: git push --force"
    if DROP_TABLE_RE.search(c):
        return "Blocked destructive SQL: DROP TABLE"
    if TRUNCATE_RE.search(c):
        return "Blocked destructive SQL: TRUNCATE"
    if DELETE_FROM_RE.search(c) and not WHERE_RE.search(c):
        return "Blocked destructive SQL: DELETE FROM without WHERE"

    return None


def _extract_command(payload: dict) -> str:
    # Different Claude Code versions may structure tool args differently.
    for key in ("command", "cmd", "input"):
        v = payload.get(key)
        if isinstance(v, str):
            return v

    tool = payload.get("tool")
    if isinstance(tool, dict):
        args = tool.get("args")
        if isinstance(args, dict):
            v = args.get("command") or args.get("cmd")
            if isinstance(v, str):
                return v
    return ""


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # If the hook can't parse input, do not break normal operation.
        return 0

    cmd = _extract_command(payload)
    reason = _classify(cmd)
    if not reason:
        return 0

    proj = _project_path(payload)
    line = f"{_now_iso()}\t{_sanitize_field(proj)}\t{_sanitize_field(cmd)}\n"
    try:
        with _blocked_log_path().open("a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # Logging failures should not change block decision.
        pass

    # Print a clear message to Claude; non-zero exit indicates "block".
    print(reason)
    print("If you intended to do this, use a safer alternative or ask for explicit confirmation.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
