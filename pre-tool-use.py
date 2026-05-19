#!/usr/bin/env python3
"""
Dangerous Command Blocker - Claude Code pre-tool-use hook.
Blocks destructive commands before execution. Safe commands pass through.

Installation:
  mkdir -p ~/.claude/hooks/pre-tool-use
  curl -sL https://raw.githubusercontent.com/niufox/claude-builders-bounty/main/pre-tool-use.py \
    -o ~/.claude/hooks/pre-tool-use/dangerous-command-blocker.py && chmod +x "$_"
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
CONFIG_FILE = os.path.expanduser("~/.claude/hooks/allowed-dangerous.json")

# ─── Safe Allowlist ──────────────────────────────────────────────
# Common build/dev cleanup patterns that use rm -rf legitimately
SAFE_RM_PATTERNS = [
    r"rm\s+-rf\s+node_modules",
    r"rm\s+-rf\s+\.next",
    r"rm\s+-rf\s+dist",
    r"rm\s+-rf\s+build",
    r"rm\s+-rf\s+target",
    r"rm\s+-rf\s+__pycache__",
    r"rm\s+-rf\s+\.venv",
    r"rm\s+-rf\s+venv",
    r"rm\s+-rf\s+\.git",
    r"rm\s+-rf\s+\.terraform",
    r"rm\s+-rf\s+\.pnpm-store",
    r"rm\s+-rf\s+\.cache",
    r"rm\s+-rf\s+coverage",
    r"rm\s+-rf\s+\.turbo",
    r"rm\s+-rf\s+\.eslintcache",
    r"rm\s+-rf\s+\.parcel-cache",
    r"rm\s+-rf\s+tmp",
    r"rm\s+-rf\s+temp",
    r"rm\s+-rf\s+logs?",
]

# Safety patterns for known destructive system commands
SAFE_SYSTEM_PATTERNS = [
    (r"\brm\s+(-[rfR]+\s+)?/", "rm / (system root)"),
    (r"\brm\s+(-[rfR]+\s+)?/\*", "rm /* (system root wildcard)"),
    (r"\bsudo\s+rm\s+(-[rfR]+\s+)?/", "sudo rm / (system root with sudo)"),
]


# ─── Dangerous Pattern Definitions ──────────────────────────────
# Format: (compiled_regex, description, severity)

DANGEROUS_PATTERNS = [
    # File system destruction
    (re.compile(r"\brm\s+(-[rfR]+|-[rf]+\s+-[rfR]+)\s*/?(?:$|\s)"), "rm -rf (recursive force delete)"),

    # Database destruction
    (re.compile(r"\bDROP\s+DATABASE\b", re.IGNORECASE), "DROP DATABASE (database deletion)"),
    (re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE), "DROP TABLE (table deletion)"),
    (re.compile(r"\bTRUNCATE\b", re.IGNORECASE), "TRUNCATE (table truncation)"),

    # Git force push
    (re.compile(r"\bgit\s+push\s+.*--force\b"), "git push --force (force push)"),
    (re.compile(r"\bgit\s+push\s+.*\s-f\b"), "git push -f (force push)"),

    # Disk/block device destruction
    (re.compile(r"\bdd\s+if=/dev/zero\b"), "dd if=/dev/zero (disk overwrite)"),
    (re.compile(r"\bdd\s+if=/dev/urandom\b"), "dd if=/dev/urandom (random disk overwrite)"),
    (re.compile(r"\bmkfs\.?\w*\b"), "mkfs (filesystem creation - destructive)"),
    (re.compile(r"\bmkswap\b"), "mkswap (swap creation - destructive)"),
    (re.compile(r"\bformat\s+\w:"), "format (drive formatting)"),

    # System shutdown / reboot
    (re.compile(r"\bshutdown\s+-[rhHP]\b"), "shutdown (system shutdown/reboot)"),
    (re.compile(r"\breboot\b"), "reboot (system restart)"),
    (re.compile(r"\bpoweroff\b"), "poweroff (system power off)"),
    (re.compile(r"\bhalt\b"), "halt (system halt)"),

    # Dangerous permission changes
    (re.compile(r"\bchmod\s+-R\s+777\b"), "chmod -R 777 (recursive dangerous permissions)"),
    (re.compile(r"\bchmod\s+777\s+-R\b"), "chmod 777 -R (recursive dangerous permissions)"),
    (re.compile(r"\bchown\s+-R\b"), "chown -R (recursive ownership change)"),

    # Piped internet scripts (curl/wget to shell)
    (re.compile(r"\b(?:curl|wget)\s+.*\s*\|\s*(?:bash|sh)\b"), "curl/wget to shell (piped script execution)"),
    (re.compile(r"\bbash\s*[<(]\s*(?:curl|wget)\b"), "bash from curl/wget subprocess"),
    (re.compile(r'\beval\s*["\'].*curl\b', re.IGNORECASE), 'eval with curl (remote code execution)'),
    (re.compile(r'\beval\s*["\'].*wget\b', re.IGNORECASE), 'eval with wget (remote code execution)'),

    # System config modification
    (re.compile(r"\b>\s+/etc/"), "write to /etc/ (system config modification)"),
    (re.compile(r"\bsudo\s+tee\s+/etc/"), "sudo tee /etc/ (privileged config write)"),

    # Fork bomb (simplified detection)
    (re.compile(r":\(\)\s*\{"), ":(){ (fork bomb pattern)"),

    # Dangerous moves
    (re.compile(r"\bmv\s+/\s+"), "mv / (moving root directory)"),

    # Package manager destructive operations
    (re.compile(r"\bapt-get\s+(remove|purge)\s+--purge\b"), "apt-get remove/purge (package removal)"),
    (re.compile(r"\bapt\s+(remove|purge|autoremove)\s+-y\b"), "apt remove -y (automatic package removal)"),
    (re.compile(r"\bpacman\s+-R[sn]+\b"), "pacman -R (package removal with dependencies)"),
    (re.compile(r"\byum\s+(remove|erase)\b"), "yum remove (package removal)"),

    # Docker destructive
    (re.compile(r"\bdocker\s+system\s+prune\s+-[af]"), "docker system prune -a (destroy all containers/images)"),
    (re.compile(r"\bdocker\s+rmi\s+-f\b"), "docker rmi -f (force remove images)"),
    (re.compile(r"\bdocker\s+volume\s+prune\s+-f\b"), "docker volume prune (destroy all volumes)"),
]

# Compile safe patterns once
COMPILED_SAFE_RM = [re.compile(p) for p in SAFE_RM_PATTERNS]


def load_allowlist():
    """Load user-defined allowlist from config file."""
    if not os.path.exists(CONFIG_FILE):
        return set()
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        return set(data.get("allowed_commands", []))
    except (json.JSONDecodeError, OSError):
        return set()


def is_safe_rm(cmd):
    """Check if rm -rf is targeting a known safe build directory."""
    for pat in COMPILED_SAFE_RM:
        if pat.search(cmd):
            return True
    return False


def has_where_clause(cmd):
    """Check if DELETE FROM has a WHERE clause."""
    dm = re.search(r"\bDELETE\s+FROM\b", cmd, re.IGNORECASE)
    if dm:
        rest = cmd[dm.end():]
        return bool(re.search(r"\bWHERE\b", rest, re.IGNORECASE))
    return True


def is_dangerous_rm_rf(cmd):
    """Check if rm -rf targets system-critical paths."""
    for pat, desc in SAFE_SYSTEM_PATTERNS:
        if pat.search(cmd):
            return True, desc
    return False, None


def check_command(cmd, allowlist):
    """Check a command against all dangerous patterns."""
    # Check allowlist first
    cmd_stripped = cmd.strip()
    if cmd_stripped in allowlist:
        return False, ""

    # Check DELETE FROM without WHERE
    if re.search(r"\bDELETE\s+FROM\b", cmd, re.IGNORECASE) and not has_where_clause(cmd):
        return True, "Blocked: DELETE FROM without WHERE clause (mass deletion)"

    # Check rm patterns
    for pat, desc in DANGEROUS_PATTERNS:
        if pat.search(cmd):
            # Special case: rm -rf common build dirs should be allowed
            if "rm -rf" in desc and is_safe_rm(cmd):
                return False, ""
            return True, f"Blocked: {desc}"

    return False, ""


def log_blocked(reason, cmd, proj):
    """Log a blocked command attempt."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {reason}\n")
        f.write(f"  Command: {cmd}\n")
        f.write(f"  Project: {proj}\n")
        f.write(f"  CWD:     {os.getcwd()}\n")
        f.write(f"  ---\n")


def get_deny_response(reason, cmd):
    """Build the deny response for Claude Code."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"{reason}. If you need to run this command, execute it manually outside Claude Code.",
            "additionalContext": (
                f"🛑 Command blocked: `{cmd}`\n\n"
                f"**Reason:** {reason}\n\n"
                f"**To bypass:** Run this command manually in your terminal outside of Claude Code.\n"
                f"**To allowlist:** Add this exact command to `~/.claude/hooks/allowed-dangerous.json`:\n"
                f'```json\n{{"allowed_commands": ["{cmd.strip()}"]}}\n```'
            )
        }
    }


def main():
    try:
        inp = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # Support both camelCase and snake_case input formats
    tool_name = (inp.get("tool_name") or inp.get("toolName") or "").lower()

    if tool_name not in ("bash", "terminal", "shell", "command_run"):
        return

    tool_input = inp.get("tool_input") or inp.get("toolInput") or {}
    command = ""

    if isinstance(tool_input, dict):
        command = tool_input.get("command", "")
        # Handle `cmd` key (used by some terminal tools)
        if not command:
            command = tool_input.get("cmd", "")
    elif isinstance(tool_input, str):
        command = tool_input

    if not command:
        return

    # Process multi-line commands
    lines = command.replace("\\\n", " ").split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Process chained commands (&&, ||, ;)
        for segment in re.split(r"\s*&&\s*|\s*\|\|\s*|\s*;\s*", line):
            segment = segment.strip()
            if not segment:
                continue

            allowlist = load_allowlist()
            bad, reason = check_command(segment, allowlist)
            if bad:
                proj = os.getcwd()
                log_blocked(reason, segment, proj)
                result = get_deny_response(reason, segment)
                print(json.dumps(result))
                return

    # Command is safe - allow it
    return


if __name__ == "__main__":
    main()
