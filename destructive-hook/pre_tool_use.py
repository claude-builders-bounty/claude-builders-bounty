#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks dangerous bash commands before execution.

Install:
    mkdir -p ~/.claude/hooks
    cp pre_tool_use.py ~/.claude/hooks/pre_tool_use.py
    chmod +x ~/.claude/hooks/pre_tool_use.py

Hook input (JSON on stdin):
    {
        "tool_name": "bash",
        "tool_input": {"command": "rm -rf /"},
        "cwd": "/project/path"
    }

Hook output (JSON on stdout):
    {"decision": "proceed"}                    # allow command
    {"decision": "block", "reason": "..."}     # block with explanation

Logs blocked attempts to ~/.claude/hooks/blocked.log with:
    [ISO8601] BLOCKED | project=/path | command="rm -rf /" | reason="..."
"""

import sys
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

# Dangerous patterns: (regex, human-readable reason)
DANGEROUS_PATTERNS = [
    # === Filesystem destruction ===
    (r"rm\s+-rf\s+/(\s|$)", "rm -rf on root directory — irreversible system destruction"),
    (r"rm\s+-rf\s+~(\s|/|$)", "rm -rf on home directory — irreversible data loss"),
    (r"rm\s+-rf\s+\*(\s|$)", "rm -rf * — mass deletion of current directory"),
    (r"rm\s+-rf\s+\.\.?(\s|/|$)", "rm -rf on parent/current directory — mass deletion"),
    (r"rm\s+-rf\s+/(etc|usr|var|opt|bin|sbin|lib|boot|dev|proc|sys|run)(\s|/|$)",
     "rm -rf on system directory — breaks OS"),
    (r">\s*/dev/(sd|hd|vd)[a-z]", "Direct write to block device — destroys filesystem"),

    # === Database destruction ===
    (r"\bDROP\s+TABLE\b", "DROP TABLE — irreversible schema + data loss"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE — destroys entire database"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE — removes all rows without WHERE"),
    (r"\bDELETE\s+FROM\s+\w+(?:\s+(?!WHERE\b).*)?\s*(?:;|$)",
     "DELETE FROM without WHERE — mass data deletion"),

    # === Dangerous git operations ===
    (r"git\s+push\s+--force(?!-with-lease)\b(?!\s+--lease)", "git push --force without --lease — overwrites remote history"),
    (r"git\s+push\s+-f\b", "git push -f — overwrites remote history"),
    (r"git\s+reset\s+--hard\b", "git reset --hard — discards uncommitted changes"),
    (r"git\s+clean\s+-[fidx]+", "git clean — removes untracked files permanently"),

    # === Permission escalation / security ===
    (r"chmod\s+777\s+[/~]", "chmod 777 on root/home — world-writable sensitive paths"),
    (r"chmod\s+-R\s+777\b", "chmod -R 777 — recursive world-writable permissions"),
    (r"chown\s+-R\s+root\b", "chown -R root — recursive ownership change to root"),

    # === Remote code execution vectors ===
    (r"curl\s+.*\|\s*(ba)?sh\b", "curl | sh — pipes remote code to shell (RCE risk)"),
    (r"wget\s+.*-O\s*-\s*\|\s*(ba)?sh\b", "wget | sh — pipes remote code to shell (RCE risk)"),
    (r"bash\s+-c\s+.*\$\(.*\)", "bash -c with command substitution — potential injection"),

    # === System compromise ===
    (r":\(\)\{\s*:\|:\s*&\s*\};:", "Fork bomb — exhausts system processes"),
    (r"\bdd\s+if=.*of=/dev/", "dd writing to device — destroys filesystem/partition"),
    (r"mkfs\.\w+\s+/dev/", "mkfs on device — formats partition (data loss)"),
    (r"fdisk\s+/dev/", "fdisk on device — modifies partition table"),
]


def log_blocked(command: str, project_path: str, reason: str) -> None:
    """Append blocked attempt to log file."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] BLOCKED | project={project_path} | command={command!r} | reason={reason}\n")


def check_command(command: str) -> tuple[bool, str]:
    """
    Returns (blocked: bool, reason: str).
    """
    for pattern, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main() -> None:
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Invalid input — allow through to avoid breaking workflow
        print(json.dumps({"decision": "proceed"}))
        return

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    project_path = hook_input.get("cwd", os.getcwd())

    # Only intercept bash/shell commands
    if tool_name not in ("bash", "shell_command", "Bash"):
        print(json.dumps({"decision": "proceed"}))
        return

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"decision": "proceed"}))
        return

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, project_path, reason)
        result = {
            "decision": "block",
            "reason": (
                f"⚠️  BLOCKED: {reason}\n\n"
                f"Command: `{command[:120]}{'...' if len(command) > 120 else ''}`\n\n"
                f"This command matches a dangerous pattern and was blocked for safety.\n"
                f"Block logged to: {LOG_FILE}\n\n"
                f"Safer alternatives:\n"
                f"- Instead of `rm -rf /path`, use `mv /path /tmp/to_delete_$(date +%s)` first\n"
                f"- Instead of `git push --force`, use `git push --force-with-lease`\n"
                f"- For DROP/TRUNCATE/DELETE, add explicit safeguards or run via migration\n"
                f"- For curl|sh, download script first, inspect, then execute"
            ),
        }
        print(json.dumps(result))
    else:
        print(json.dumps({"decision": "proceed"}))


if __name__ == "__main__":
    main()