
#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Destructive Command Guard.

Intercepts dangerous bash commands before execution and blocks them.
Logs every blocked attempt with timestamp, command, and project path.

Installation:
  Copy this file to ~/.claude/hooks/pre-tool-use.py
  chmod +x ~/.claude/hooks/pre-tool-use.py

Claude Code hooks format: reads JSON from stdin, outputs JSON to stdout.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Destructive command patterns (regex)
# ---------------------------------------------------------------------------

DESTRUCTIVE_PATTERNS = [
    # rm -rf / variants
    (re.compile(r'\brm\s+.*-(?:r|f).*/(?:$|\s)'), "rm -rf against root"),
    (re.compile(r'\brm\s+.*--no-preserve-root'), "rm --no-preserve-root detected"),
    (re.compile(r'\brm\s+-[a-z]*[rf][a-z]*r?\s+/\b'), "rm -rf / detected"),

    # SQL destructive operations
    (re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE), "DROP TABLE"),
    (re.compile(r'\bDROP\s+DATABASE\b', re.IGNORECASE), "DROP DATABASE"),
    (re.compile(r'\bTRUNCATE\s+(TABLE\s+)?\w+', re.IGNORECASE), "TRUNCATE TABLE"),
    (re.compile(r'\bDELETE\s+FROM\s+\w+\s*(?!.*\bWHERE\b)', re.IGNORECASE),
     "DELETE FROM without WHERE clause"),

    # Git destructive
    (re.compile(r'\bgit\s+push\s+.*(?:--force|--force-with-lease)\b'),
     "git push --force"),
    (re.compile(r'\bgit\s+reset\s+--hard\b'), "git reset --hard"),

    # Filesystem destructive
    (re.compile(r'\b(?:mkfs|mkswap|swapon|fdisk|parted|dd\s+if=)\b'),
     "Low-level disk operation"),
    (re.compile(r'>\s*/dev/(?:sd[a-z]+|nvme\dn\d|mmcblk\d)'),
     "Overwriting block device"),

    # Shell destructive
    (re.compile(r'\bchmod\s+777\s+/'), "chmod 777 on root path"),
    (re.compile(r'\bchown\s+-R\s+\w+:\w+\s+/\b'), "recursive chown from root"),
    (re.compile(r':\s*\(\)\s*\{\s*.*\|.*\}'), "Potential fork bomb pattern"),

    # Docker / container
    (re.compile(r'\bdocker\s+(?:rm|rmi|system\s+prune)\b.*-f'),
     "Docker force removal"),

    # Powershell destructive
    (re.compile(r'\bRemove-Item\s+.*-Recurse\s+.*-Force\b', re.IGNORECASE),
     "PowerShell Remove-Item -Recurse -Force"),
    (re.compile(r'\brmdir\s+/[sS]\s+/[qQ]\s+C:\\', re.IGNORECASE),
     "rmdir /s /q on C: drive"),

    # Format / partition
    (re.compile(r'\bformat\s+[A-Za-z]:\b', re.IGNORECASE),
     "format drive command"),
]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


def log_block(command: str, reason: str, project_path: str = ""):
    """Log a blocked command attempt."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command[:500],
        "reason": reason,
        "project": project_path or os.getcwd(),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Hook entry point
# ---------------------------------------------------------------------------

def main():
    """Read hook input from stdin, check command, output decision."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            # No input — allow (hook called without context)
            print(json.dumps({"continue": True}))
            return

        hook_input = json.loads(raw)
    except json.JSONDecodeError:
        # Invalid JSON — allow (safety: don't block unknown format)
        print(json.dumps({"continue": True}))
        return

    # Extract the command to execute
    command = hook_input.get("command", "")
    if isinstance(command, list):
        command = " ".join(command)

    project_path = hook_input.get("project_path", hook_input.get("cwd", ""))

    if not command or not command.strip():
        print(json.dumps({"continue": True}))
        return

    # Check against destructive patterns
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            log_block(command, reason, str(project_path))

            message = (
                f"🚫 DESTRUCTIVE COMMAND BLOCKED: {reason}\n"
                f"   Command: {command[:200]}\n"
                f"   This command could cause irreversible data loss.\n"
                f"   If you're sure, review the command and use --force-override\n"
                f"   or run it manually in a terminal outside Claude Code.\n"
                f"   Logged to: {LOG_FILE}"
            )

            print(json.dumps({
                "continue": False,
                "stop_reason": message,
            }, ensure_ascii=False))
            return

    # Command is safe — allow
    print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
