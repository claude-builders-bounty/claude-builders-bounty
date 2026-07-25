#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — intercepts dangerous bash commands.

Install:
  mkdir -p ~/.claude/hooks
  cp pre_tool_use.py ~/.claude/hooks/
  claude config set hooks.pre_tool_use ~/.claude/hooks/pre_tool_use.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Patterns that are ALWAYS blocked — no exceptions
DESTRUCTIVE_PATTERNS = [
    # Filesystem nuking
    re.compile(r"\brm\s+-rf\s+[/*~$]"),
    re.compile(r"\brm\s+--no-preserve-root\b"),
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+if=/dev/"),
    re.compile(r"\bdd\s+of=/dev/"),
    re.compile(r"\bformat\s+[a-z]:[/\\]"),
    re.compile(r"\bmkswap\b"),
    # Git destruction
    re.compile(r"\bgit\s+push\s+-f\b"),
    re.compile(r"\bgit\s+push\s+--force\b"),
    re.compile(r"\bgit\s+reset\s+--hard\s+HEAD~"),
    re.compile(r"\bgit\s+clean\s+-f[dx]?\b"),
    re.compile(r"\bgit\s+filter-branch\b"),
    # System destruction
    re.compile(r"\bchmod\s+-R\s+0\b"),
    re.compile(r"\bchown\s+-R\s+"),
    re.compile(r"\bsudo\s+rm\b"),
    # Docker destruction
    re.compile(r"\bdocker\s+system\s+prune\s+-a\b"),
    re.compile(r"\bdocker\s+rmi\s+-f\b"),
    # Dangerous eval
    re.compile(r"\beval\s+\$\(.*\)"),
    re.compile(r"\bexec\s+\$\(.*\)"),
]

# UPDATE/DELETE queries must include WHERE
SQL_DANGER = re.compile(
    r"\b(DELETE\s+FROM|UPDATE\s+\w+|DROP\s+TABLE|TRUNCATE\s+TABLE|ALTER\s+TABLE)\b",
    re.IGNORECASE,
)

# Patterns that trigger REVIEW mode (warn but allow with confirmation)
REVIEW_PATTERNS = [
    re.compile(r"\bgit\s+push\b"),
    re.compile(r"\bnpm\s+publish\b"),
    re.compile(r"\bnpm\s+unpublish\b"),
    re.compile(r"\bdotnet\s+nuget\s+push\b"),
    re.compile(r"\btwine\s+upload\b"),
    re.compile(r"\bgh\s+release\s+create\b"),
    re.compile(r"\bdanger\s+--danger_id\b"),
    re.compile(r"\bwget\s+.*[|;]\s*(sh|bash)\b"),
    re.compile(r"\bcurl\s+.*[|;]\s*(sh|bash)\b"),
    re.compile(r"\bchmod\s+\+x\b"),
    re.compile(r"\brm\s+-rf\b(?!\s+[/*~$])"),
]

# Config files — warn before write
CONFIG_FILES = [
    "package.json", ".env", ".env.local", ".npmrc", ".gitconfig",
    "tsconfig.json", "next.config", "docker-compose", "Dockerfile",
    "nginx.conf", ".htaccess", "webpack.config", "vite.config",
]


def log_blocked(cmd: str, reason: str, project: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] BLOCKED | project={project} | reason={reason} | cmd={cmd[:300]}\n")


def check_sql_safety(cmd: str) -> tuple[bool, str]:
    """Check if SQL has a WHERE clause where required."""
    m = SQL_DANGER.search(cmd)
    if not m:
        return True, ""
    remaining = cmd[m.end():]
    if "WHERE" not in remaining.upper() and "LIMIT" not in remaining.upper():
        return False, f"DANGER: '{m.group(1)}' without WHERE — would affect ALL rows"
    return True, ""


def check_destructive(cmd: str) -> tuple[bool, str]:
    for pat in DESTRUCTIVE_PATTERNS:
        if pat.search(cmd):
            return False, f"BLOCKED: destructive pattern '{pat.pattern}'"
    safe, reason = check_sql_safety(cmd)
    if not safe:
        return False, reason
    return True, ""


def check_review(cmd: str) -> list[str]:
    warnings = []
    for pat in REVIEW_PATTERNS:
        if pat.search(cmd):
            warnings.append(f"REVIEW: '{pat.pattern}' — confirm intent")
    for cfg in CONFIG_FILES:
        if cfg in cmd:
            warnings.append(f"REVIEW: modifying '{cfg}' — verify changes")
    return warnings


def check_config_edit(cmd: str) -> list[str]:
    """Warn about editing config files."""
    warnings = []
    # Writing to config files
    for cfg in CONFIG_FILES:
        if cfg in cmd and any(cmd.strip().startswith(x) for x in [">", ">>", "echo", "cat >", "printf"]):
            warnings.append(f"REVIEW: writing to '{cfg}' — confirm correctness")
    # SCP/rsync to remote
    if re.search(r"\b(scp|rsync)\s+\S+@\S+:", cmd):
        warnings.append("REVIEW: remote transfer — verify destination")
    return warnings


def main():
    try:
        payload = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, IndexError):
        print(json.dumps({"isAllowed": True}))
        return

    cmd = payload.get("command", "")
    if not cmd:
        print(json.dumps({"isAllowed": True}))
        return

    tool = payload.get("tool", "")
    if tool not in ("Bash", "bash", "ExecuteCommand", ""):
        print(json.dumps({"isAllowed": True}))
        return

    project = payload.get("projectPath", os.getcwd())

    # 1. Check destructive patterns (hard block)
    safe, reason = check_destructive(cmd)
    if not safe:
        log_blocked(cmd, reason, project)
        print(json.dumps({
            "isAllowed": False,
            "message": (f"⛔ SAFETY HOOK: {reason}\n\n"
                       f"Blocked and logged to {LOG_FILE}\n"
                       f"Confirm with a human before retrying."),
        }))
        return

    # 2. Check review patterns (warning but allow)
    warnings = check_review(cmd) + check_config_edit(cmd)
    if warnings:
        result = {
            "isAllowed": True,
            "message": "⚠️ " + "\n⚠️ ".join(warnings),
        }
    else:
        result = {"isAllowed": True}

    print(json.dumps(result))


if __name__ == "__main__":
    main()
