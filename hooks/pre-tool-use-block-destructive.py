#!/usr/bin/env python3
"""
Pre-tool-use hook that blocks destructive bash commands in Claude Code.

Install: cp pre-tool-use-block-destructive.py ~/.claude/hooks/
Make executable: chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.py

Hook format: reads JSON from stdin, exits 0 to allow or 2 to block.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

BLOCKED_PATTERNS = [
    # Filesystem destruction
    (re.compile(r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]*r[a-zA-Z]*\s+).*(?<!\s\.)\S", re.IGNORECASE), "rm with -f/-r flags on non-dot paths"),
    (re.compile(r"\brm\s+-[a-zA-Z]*rf[a-zA-Z]*\s+", re.IGNORECASE), "rm -rf"),
    (re.compile(r"\bmkfs\b", re.IGNORECASE), "mkfs (filesystem format)"),
    (re.compile(r"\bdd\s+.*of=/dev/", re.IGNORECASE), "dd writing to device"),
    (re.compile(r"\bformat\s+[A-Z]:", re.IGNORECASE), "disk format"),
    (re.compile(r">/dev/sd[a-z]", re.IGNORECASE), "direct device write"),
    (re.compile(r"\bshred\b", re.IGNORECASE), "shred (secure delete)"),

    # Database destruction
    (re.compile(r"\bDROP\s*(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "DROP TABLE/DATABASE/SCHEMA"),
    (re.compile(r"\bTRUNCATE\s*(TABLE\s+)?\w+", re.IGNORECASE), "TRUNCATE"),
    (re.compile(r"\bDELETE\s+FROM\b(?!\s*\w+\s*(--\s*)?WHERE\b)", re.IGNORECASE), "DELETE FROM without WHERE"),

    # Git force operations
    (re.compile(r"\bgit\s+push\s+.*--force", re.IGNORECASE), "git push --force"),
    (re.compile(r"\bgit\s+push\s+-f\b", re.IGNORECASE), "git push -f"),
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "git reset --hard"),
    (re.compile(r"\bgit\s+clean\s+-[a-zA-Z]*f", re.IGNORECASE), "git clean -f"),
    (re.compile(r"\bgit\s+checkout\s+--\s*\.", re.IGNORECASE), "git checkout -- . (discard all)"),

    # Permission changes
    (re.compile(r"\bchmod\s+(-R\s+)?777\b", re.IGNORECASE), "chmod 777"),
    (re.compile(r"\bchmod\s+(-R\s+)?000\b", re.IGNORECASE), "chmod 000 (lock out)"),

    # Fork bomb (matches :(){:|:&} and variants)
    (re.compile(r":\s*\(\s*\)\s*\{.*\|.*&", re.IGNORECASE), "fork bomb"),

    # Shutdown/reboot
    (re.compile(r"\b(shutdown|reboot|poweroff|halt)\s+", re.IGNORECASE), "shutdown/reboot"),

    # Overwrite critical files
    (re.compile(r">\s*/etc/(passwd|shadow|sudoers|fstab)", re.IGNORECASE), "overwriting system config"),
    (re.compile(r">\s*/boot/", re.IGNORECASE), "overwriting boot files"),

    # Kill all
    (re.compile(r"\bkill\s+(-9\s+)?-1\b", re.IGNORECASE), "kill -1 (all processes)"),
    (re.compile(r"\bkillall\b", re.IGNORECASE), "killall"),

    # Container/orchestration destruction
    (re.compile(r"\bdocker\s+system\s+prune", re.IGNORECASE), "docker system prune"),
    (re.compile(r"\bkubectl\s+delete\s+(namespace|cluster)", re.IGNORECASE), "kubectl delete namespace/cluster"),

    # Network destruction
    (re.compile(r"\biptables\s+-F\b", re.IGNORECASE), "iptables flush"),
    (re.compile(r"\bip\s+(addr|link)\s+(del|flush)", re.IGNORECASE), "network interface delete"),
]

# Patterns that are explicitly allowed (whitelist overrides)
ALLOWED_PATTERNS = [
    re.compile(r"\brm\s+(-rf|-r|-f)?\s+.*\.(log|tmp|cache|pyc)\b", re.IGNORECASE),  # temp files ok
    re.compile(r"\brm\s+(-rf|-r|-f)?\s+/tmp/\S+", re.IGNORECASE),  # /tmp ok
    re.compile(r"\brm\s+(-rf|-r|-f)?\s+(\./)?node_modules(/\S+)?\b", re.IGNORECASE),  # ./node_modules ok (explicit relative)
    re.compile(r"\bgit\s+push\s+.*--force-with-lease", re.IGNORECASE),  # force-with-lease is safer
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")


# Patterns indicating shell expansion/substitution that could bypass checks
SHELL_EXPANSION_PATTERNS = [
    re.compile(r'\$\('),           # $(command)
    re.compile(r'`'),              # `command`
    re.compile(r'\$\{'),          # ${variable}
    re.compile(r'\$[A-Za-z_]'),   # $VAR
    re.compile(r'\|\|'),          # || chaining
    re.compile(r'&&'),             # && chaining
    re.compile(r';\s*\w'),       # ; command chaining
]


def normalize_command(cmd: str) -> str:
    """Strip comments and decode common escape patterns."""
    # Remove inline comments (but preserve strings)
    cmd = re.sub(r'(?<!["\'])#[^\n]*$', '', cmd)
    # Remove C-style comments
    cmd = re.sub(r'/\*.*?\*/', '', cmd)
    # Normalize whitespace
    cmd = re.sub(r'\s+', ' ', cmd).strip()
    return cmd


def has_shell_expansion(command: str) -> bool:
    """Check if command uses shell expansion that could bypass pattern checks."""
    for pattern in SHELL_EXPANSION_PATTERNS:
        if pattern.search(command):
            return True
    return False


def is_blocked(command: str) -> tuple[bool, str]:
    """Check if a command should be blocked. Returns (blocked, reason)."""
    normalized = normalize_command(command)

    # Check whitelist first
    for pattern in ALLOWED_PATTERNS:
        if pattern.search(normalized):
            return False, ""

    for pattern, reason in BLOCKED_PATTERNS:
        if pattern.search(normalized):
            return True, reason

    return False, ""


def log_blocked(command: str, reason: str):
    """Log blocked attempt to file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project = os.getcwd()
    log_line = f"{timestamp} | BLOCKED | reason={reason} | cmd={command.strip()} | cwd={project}\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse, allow

    # Claude Code hooks format: check if tool is Bash
    tool_name = data.get("tool_name", "")
    if tool_name.lower() not in ("bash", "shell", "terminal"):
        sys.exit(0)  # Only check bash commands

    # Extract command from tool input
    tool_input = data.get("tool_input", {})
    command = ""
    if isinstance(tool_input, dict):
        command = tool_input.get("command", "") or tool_input.get("content", "")
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        sys.exit(0)

    blocked, reason = is_blocked(command)

    # If command has shell expansion, also check for destructive patterns in expanded form
    if not blocked and has_shell_expansion(command):
        # Block if shell expansion is combined with any destructive-looking command
        for pattern, desc in BLOCKED_PATTERNS:
            if pattern.search(command):
                blocked = True
                reason = f"{desc} (via shell expansion)"
                break
        if not blocked:
            # Warn about shell expansion but allow
            pass  # Shell expansion alone isn't destructive

    if blocked:
        log_blocked(command, reason)
        # Use ASCII-safe output for Windows compatibility
        print(f"[BLOCKED] {reason}")
        print(f"The command '{command.strip()}' was blocked to prevent accidental damage.")
        print("If you really need to run this, please confirm with the user first.")
        sys.exit(2)  # Exit code 2 = block
    else:
        sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
