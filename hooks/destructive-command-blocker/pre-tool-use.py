#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook: Destructive Command Blocker
Intercepts and halts high-risk bash commands:
- rm -rf, rm -fr, rm --recursive --force (and variations, subshells, sudo)
- DROP TABLE / DROP DATABASE / DROP SCHEMA
- git push --force / -f / --force-with-lease / +branch
- TRUNCATE / TRUNCATE TABLE
- DELETE FROM without WHERE clause

Logs all blocked attempts to ~/.claude/hooks/blocked.log with timestamp, working directory, and command context.
Zero-dependency, Python 3.8+ compatible.
"""

import sys
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Tuple

HOOKS_DIR = Path.home() / ".claude" / "hooks"
LOG_FILE = HOOKS_DIR / "blocked.log"

BLOCKED_PATTERNS = [
    # 1. rm -rf variants (rm -rf, rm -fr, rm -r -f, rm --recursive --force, sudo rm -rf, etc.)
    (
        re.compile(
            r"\brm\s+.*?(?:-[a-zA-Z]*[rf][a-zA-Z]*|--recursive\s+--force|--force\s+--recursive|-r\s+--force|--force\s+-r)\b",
            re.IGNORECASE
        ),
        "Recursive force removal ('rm -rf') detected. High risk of irrecoverable data loss."
    ),
    # 2. DROP TABLE / DROP DATABASE / DROP SCHEMA (SQL)
    (
        re.compile(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
        "Database destructive command ('DROP TABLE/DATABASE/SCHEMA') detected."
    ),
    # 3. git push --force (or git push -f, --force-with-lease, +branch)
    (
        re.compile(r"\bgit\s+push\b.*?\s+(?:--force|-f\b|--force-with-lease\b|\+\w+)", re.IGNORECASE),
        "Remote repository history rewrite ('git push --force') detected."
    ),
    # 4. TRUNCATE (SQL TRUNCATE / TRUNCATE TABLE)
    (
        re.compile(r"\bTRUNCATE(?:\s+TABLE)?\s+[a-zA-Z0-9_`\"']+", re.IGNORECASE),
        "Database table purge ('TRUNCATE') detected."
    ),
    # 5. DELETE FROM without WHERE clause
    (
        re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"']+(?!\s+WHERE\b)[^;]*;?", re.IGNORECASE),
        "Unbounded table deletion ('DELETE FROM' without WHERE clause) detected."
    )
]

def unwrap_command(cmd: str) -> str:
    """Strips execution wrappers like sudo, env, nohup, bash -c, sh -c."""
    unwrapped = cmd.strip()
    # Strip sudo / nohup / env wrappers
    unwrapped = re.sub(r"^(?:sudo\s+(?:-u\s+\S+\s+)?|nohup\s+|env\s+)+", "", unwrapped, flags=re.IGNORECASE)
    # Extract inner command if wrapped in bash -c "..." or sh -c '...'
    m = re.match(r"^(?:bash|sh|zsh)\s+-c\s+[\"'](.*)[\"']$", unwrapped, flags=re.IGNORECASE)
    if m:
        unwrapped = m.group(1)
    return unwrapped

def check_delete_from_without_where(cmd: str) -> bool:
    """Special check for DELETE FROM lacking a WHERE clause."""
    delete_matches = re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_`\"']+)([^;]*)(?:;|$)", cmd, re.IGNORECASE)
    for m in delete_matches:
        clause = m.group(2)
        if not re.search(r"\bWHERE\b", clause, re.IGNORECASE):
            return True
    return False

def check_command(raw_cmd: str) -> Tuple[bool, str]:
    """Evaluates raw command and its sub-commands against security policies."""
    # Split compound commands (&&, ||, ;, |)
    sub_commands = re.split(r"(?:&&|\|\||;|\|)", raw_cmd)
    for sub in sub_commands:
        clean = unwrap_command(sub)
        for pattern, reason in BLOCKED_PATTERNS[:4]:
            if pattern.search(clean):
                return True, reason
        if check_delete_from_without_where(clean):
            return True, "Unbounded table deletion ('DELETE FROM' without WHERE clause) detected."
            
    return False, ""

def log_blocked_command(cmd: str, cwd: str, reason: str):
    """Logs blocked attempt to ~/.claude/hooks/blocked.log with ISO timestamp and context."""
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()
        log_entry = (
            f"[{timestamp}] BLOCKED\n"
            f"  Command:      {cmd.strip()}\n"
            f"  Project Path: {cwd}\n"
            f"  Reason:       {reason}\n"
            f"{'-' * 60}\n"
        )
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[pre-tool-use-hook] Warning: Could not write to log: {e}\n")

def main():
    cmd = ""
    cwd = os.getcwd()
    dry_run = False

    # CLI arguments inspection
    if len(sys.argv) > 1:
        if "--dry-run" in sys.argv:
            dry_run = True
            sys.argv.remove("--dry-run")
        if "--self-test" in sys.argv:
            assert check_command("rm -rf /example")[0]
            assert check_command("DROP TABLE users")[0]
            assert check_command("git push --force origin main")[0]
            assert not check_command("echo hello")[0]
            print("Hook self-test: OK (compiled regex rules: 5)")
            sys.exit(0)
        cmd = " ".join(sys.argv[1:])
    else:
        # Check stdin for JSON payload or raw command
        if not sys.stdin.isatty():
            raw_input = sys.stdin.read().strip()
            if raw_input:
                try:
                    payload = json.loads(raw_input)
                    if isinstance(payload, dict):
                        cmd = payload.get("command") or payload.get("tool_input", {}).get("command") or raw_input
                        cwd = payload.get("cwd") or payload.get("tool_input", {}).get("cwd") or cwd
                    else:
                        cmd = raw_input
                except Exception:
                    cmd = raw_input

    if not cmd.strip():
        sys.exit(0)

    is_blocked, reason = check_command(cmd)
    if is_blocked:
        log_blocked_command(cmd, cwd, reason)
        sys.stderr.write(
            f"\n🚨 [BLOCKED BY CLAUDE HOOK] Destructive Command Intercepted!\n"
            f"Reason: {reason}\n"
            f"Command: {cmd}\n"
            f"Action: Execution halted. Modification logged to {LOG_FILE}\n\n"
        )
        if dry_run:
            print(json.dumps({"blocked": True, "reason": reason, "dry_run": True}))
            sys.exit(0)
        sys.exit(2)

    if dry_run:
        print(json.dumps({"blocked": False, "dry_run": True}))
    sys.exit(0)

if __name__ == "__main__":
    main()
