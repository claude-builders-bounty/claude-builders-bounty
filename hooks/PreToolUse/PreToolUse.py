#!/usr/bin/env python3
"""
PreToolUse hook: blocks destructive bash commands before execution.
Claude Code hooks format: https://docs.anthropic.com/claude-code/hooks

Install (2 commands):
  mkdir -p ~/.claude/hooks && cp PreToolUse.py ~/.claude/hooks/
  # then reference it in settings.json: "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/PreToolUse.py"}]}]}

Output contract:
  - JSON on stdout: {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "block"|"allow", "permissionDecisionReason": "..."}}
  - exit 0 = allow, exit 2 = block (see docs); we use the JSON permissionDecision for explicit control.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Dangerous patterns (matched against the full bash command)
# ---------------------------------------------------------------------------
DANGEROUS_PATTERNS = [
    # rm -rf / dangerous recursive force deletes
    (re.compile(r'\brm\s+(-{1,2}[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b|\brm\s+-rf\b', re.IGNORECASE),
     "rm -rf / recursive force delete"),
    # rm with -r or -f targeting root / home / critical paths
    (re.compile(r'\brm\s+(-{1,2}[rf]+)?\s*(/\s*(\*\s*)?|~\s*(\*\s*)?|/home|/etc|/var|/usr|/boot)\b', re.IGNORECASE),
     "rm targeting critical system path"),
    # DROP TABLE / DROP DATABASE
    (re.compile(r'\bDROP\s+(TABLE|DATABASE|SCHEMA)\b', re.IGNORECASE),
     "DROP TABLE/DATABASE/SCHEMA"),
    # TRUNCATE
    (re.compile(r'\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z_][a-zA-Z0-9_]*', re.IGNORECASE),
     "TRUNCATE table"),
    # DELETE FROM without WHERE (allow DELETE ... WHERE)
    (re.compile(r'\bDELETE\s+FROM\s+[^\s;]+(?![^;]*\bWHERE\b)', re.IGNORECASE),
     "DELETE FROM without WHERE clause"),
    # git push --force / -f
    (re.compile(r'\bgit\s+push\s+.*(--force|-f)\b', re.IGNORECASE),
     "git push --force"),
    # git reset --hard
    (re.compile(r'\bgit\s+reset\s+--hard\b', re.IGNORECASE),
     "git reset --hard"),
    # dd to disk devices
    (re.compile(r'\bdd\s+.*\bof=\s*/dev/(sd[a-z]+|nvme[0-9n]+|hd[a-z]+|vd[a-z]+)\b', re.IGNORECASE),
     "dd writing directly to a disk device"),
    # mkfs / format
    (re.compile(r'\b(mkfs\.[a-z0-9]+|mkfs|format)\b', re.IGNORECASE),
     "filesystem format (mkfs)"),
    # chmod -R 777 on critical paths
    (re.compile(r'\bchmod\s+(-R\s+)?777\s+(/|~|/etc|/var|/usr|/home)', re.IGNORECASE),
     "chmod 777 on critical path"),
    # shutdown / reboot / halt
    (re.compile(r'\b(shutdown|reboot|halt|poweroff|init\s+0|init\s+6)\b', re.IGNORECASE),
     "shutdown/reboot/halt"),
    # curl | sh / wget | sh (remote code execution)
    (re.compile(r'\b(curl|wget)\b.*\|\s*(sudo\s+)?(ba)?sh\b', re.IGNORECASE),
     "remote script piped to shell (curl|sh)"),
]

# Commands that are safe to always allow (fast path — never false-positive)
SAFE_PREFIXES = ("git status", "git log", "git diff", "ls ", "cat ", "pwd", "echo ",
                 "cd ", "python3 --version", "node --version", "which ", "find ",
                 "grep ", "head ", "tail ", "wc ", "date", "whoami", "env", "printenv")

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_block(command: str, reason: str, cwd: str) -> None:
    """Append a structured log line for every blocked attempt."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = json.dumps({
            "timestamp": ts,
            "command": command,
            "reason": reason,
            "project_path": cwd,
        }, ensure_ascii=False)
        with open(LOG_FILE, "a") as f:
            f.write(entry + "\n")
    except Exception:
        pass  # logging must never break the hook


def check_command(command: str) -> tuple[bool, str]:
    """Return (blocked, reason)."""
    cmd = command.strip()
    if not cmd:
        return False, ""
    # Fast path: obviously safe commands
    for prefix in SAFE_PREFIXES:
        if cmd.startswith(prefix):
            return False, ""
    # Danger patterns
    for pattern, reason in DANGEROUS_PATTERNS:
        if pattern.search(cmd):
            return True, reason
    return False, ""


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    # Claude Code passes tool input JSON on stdin for PreToolUse hooks
    tool_input = payload.get("tool_input") or {}
    # The bash command can arrive as tool_input.command (Bash) or in tool_use
    command = tool_input.get("command") or payload.get("tool_use", {}).get("input", {}).get("command") or ""
    cwd = payload.get("cwd") or payload.get("tool_use", {}).get("cwd") or os.getcwd()

    if not command:
        # Nothing to evaluate -> allow
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "No command to evaluate",
        }}))
        return 0

    blocked, reason = check_command(command)
    if blocked:
        log_block(command, reason, cwd)
        msg = (
            f"⛔ BLOCKED by security hook: {reason}\n"
            f"Command: {command}\n"
            f"Reason: {reason}\n"
            f"Logged to: {LOG_FILE}\n"
            f"Refusing to run destructive command. If this is intentional, "
            f"split it into a safer equivalent or confirm manually."
        )
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "block",
            "permissionDecisionReason": msg,
        }}))
        return 2

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": "Command is safe",
    }}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
