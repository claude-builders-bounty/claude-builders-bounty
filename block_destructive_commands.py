#!/usr/bin/env python3
import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

RULES = [
    (
        r'(?:^|[;&|\s])rm\s+.*?(?:-[a-zA-Z]*[rf][a-zA-Z]*[rf]|--recursive|--force)',
        "unrestricted recursive removal (rm -rf)"
    ),
    (
        r'\bDROP\s+TABLE\b',
        "destructive schema deletion (DROP TABLE)"
    ),
    (
        r'\bTRUNCATE(?:\s+TABLE)?\b',
        "table truncation (TRUNCATE)"
    ),
    (
        r'\bgit\s+push\b.*?(?:--force|-f\b)',
        "forced history rewrite (git push --force)"
    )
]

def is_dangerous(cmd: str) -> tuple[bool, str]:
    if not cmd:
        return False, ""

    # Check rm variants
    if re.search(r'(?:^|[;&|\s])rm\s+.*?-[a-zA-Z]*r\b.*?-[a-zA-Z]*f\b', cmd, re.I) or \
       re.search(r'(?:^|[;&|\s])rm\s+.*?-[a-zA-Z]*f\b.*?-[a-zA-Z]*r\b', cmd, re.I) or \
       re.search(r'(?:^|[;&|\s])rm\s+.*?--recursive.*?--force', cmd, re.I):
        return True, "unrestricted recursive removal (rm -rf)"

    for pattern, reason in RULES:
        if re.search(pattern, cmd, re.I):
            return True, reason

    # Check DELETE FROM without WHERE
    if re.search(r'\bDELETE\s+FROM\b', cmd, re.I):
        if not re.search(r'\bWHERE\b', cmd, re.I):
            return True, "unbounded row deletion (DELETE without WHERE)"

    return False, ""

def log_event(cmd: str, reason: str, cwd: str):
    log_dir = Path.home() / ".claude" / "hooks"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "blocked.log"

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {cwd} | {reason} -> {cmd}\n")

def parse_input() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:])
    
    if not sys.stdin.isatty():
        raw = sys.stdin.read().strip()
        if not raw:
            return ""
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                return payload.get("command") or payload.get("tool_input", {}).get("command", "")
        except json.JSONDecodeError:
            return raw
    return ""

def main():
    command = parse_input()
    if not command:
        sys.exit(0)

    cwd = os.getcwd()
    blocked, reason = is_dangerous(command)

    if blocked:
        log_event(command, reason, cwd)
        sys.stderr.write(f"\n[hook-blocked] Destructive command intercepted: {reason}\n")
        sys.stderr.write(f"Command: {command}\n")
        sys.stderr.write("Logged to: ~/.claude/hooks/blocked.log\n\n")
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
