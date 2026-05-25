#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks dangerous bash commands.

Installation:
    mkdir -p ~/.claude/hooks/
    cp pre-tool-use.py ~/.claude/hooks/
    chmod +x ~/.claude/hooks/pre-tool-use.py

This hook is called before every bash tool invocation in Claude Code.
It checks the command against a blocklist of dangerous patterns
and rejects execution with a clear explanation.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

BLOCKLIST_PATTERNS = [
    # Destructive file operations
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\b', "Dangerous recursive force delete detected"),
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s+/\b', "Root filesystem delete blocked"),
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s+/var\b', "System directory delete blocked"),
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s+/etc\b', "System directory delete blocked"),
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s+/home\b', "Home directory delete blocked"),
    (r'(?i)\brm\s+(-rf|--recursive\s+--force|-r\s+-f|-f\s+-r)\s+/root\b', "Root home delete blocked"),
    
    # Dangerous git operations
    (r'(?i)\bgit\s+push\s+--force\b', "Force push blocked — use 'git push --force-with-lease' instead"),
    (r'(?i)\bgit\s+push\s+-f\b', "Force push blocked — use 'git push --force-with-lease' instead"),
    (r'(?i)\bgit\s+reset\s+--hard\s+HEAD\b', "Hard reset blocked — you'll lose uncommitted changes"),
    (r'(?i)\bgit\s+reset\s+--hard\s+origin\b', "Hard reset to origin blocked — will discard local changes"),
    
    # Database dangerous operations
    (r'(?i)\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|PROCEDURE|FUNCTION)\b', "DROP statement blocked — destructive database operation"),
    (r'(?i)\bTRUNCATE\b', "TRUNCATE blocked — destructive table operation"),
    (r'(?i)\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "DELETE without WHERE clause blocked — would affect all rows"),
    (r'(?i)\bUPDATE\s+\w+\s+SET\b(?!.*\bWHERE\b)', "UPDATE without WHERE clause blocked — would affect all rows"),
    (r'(?i)\bALTER\s+(TABLE|DATABASE)\s+\w+\s+DROP\b', "ALTER DROP blocked — destructive schema change"),
    
    # System dangerous operations
    (r'(?i)\bdd\s+if=', "dd blocked — direct disk write detected"),
    (r'(?i)\bmkfs\.\w+\b', "Filesystem creation blocked"),
    (r'(?i)\b(?:fdisk|parted|gdisk)\b', "Partition table manipulation blocked"),
    (r'(?i)\bchmod\s+-?R?\s*0\b', "chmod 0 blocked — would make files unreadable"),
    (r'(?i)\bchown\s+-R\b', "Recursive chown blocked — potentially destructive"),
    
    # Package manager dangerous operations
    (r'(?i)\b(?:apt|apt-get|yum|dnf|pacman)\s+(?:remove|purge|autoremove)\b', "Package removal blocked — use only if you're sure"),
    (r'(?i)\bnpm\s+(?:uninstall|remove|rm|prune)\b', "npm uninstall blocked — use only if intended"),
    (r'(?i)\bpip\s+uninstall\b', "pip uninstall blocked — use only if intended"),
    
    # Network dangerous commands
    (r'(?i)\b(?:shutdown|reboot|halt|poweroff|init\s+0|init\s+6)\b', "System shutdown/reboot blocked"),
    (r'(?i)\bkill\s+-9\b', "SIGKILL all blocked — use targeted process termination"),
    (r'(?i)\bkillall\b', "killall blocked — use specific PID instead"),
    
    # Formatting dangerous operations
    (r'(?i)\b(?:mkfs|mkswap|swapon|swapoff)\b', "Filesystem/swap operation blocked"),
    
    # Disk/volume operations
    (r'(?i)\b(?:pvcreate|vgcreate|lvcreate|pvremove|vgremove|lvremove)\b', "LVM operation blocked"),
    
    # Sudo escalation (guard against privilege elevation)
    (r'(?i)\bsudo\s+rm\s+-rf\b', "sudo recursive delete blocked"),
    (r'(?i)\bsudo\s+\w+\s+(?!-u\b)(?!-i\b)(?!-s\b)', "sudo command with high privileges — proceed with caution"),
    
    # Write to sensitive paths
    (r'(?i)\b(?:>|>>)\s*/\s*etc\b', "Write to /etc blocked — system configuration"),
    (r'(?i)\b(?:>|>>)\s*/\s*boot\b', "Write to /boot blocked — boot partition"),
    (r'(?i)\b(?:>|>>)\s*/\s*dev\b', "Write to /dev blocked — device files"),
    
    # Crypto/encryption operations
    (r'(?i)\b(?:cryptsetup|dm-crypt|luks)\b', "Encryption operation blocked"),
]

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# ── Hook Entry ───────────────────────────────────────────────────────────────

def main():
    """Pre-tool-use hook entry point.
    
    Claude Code passes the tool invocation as JSON on stdin.
    Format: {"tool": {"name": "Bash", "input": {"command": "..."}}}
    """
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
    except (json.JSONDecodeError, EOFError):
        return json.dumps({"is_allowed": True})
    
    tool = payload.get("tool", {})
    name = tool.get("name", "")
    cmd = tool.get("input", {}).get("command", "") if isinstance(tool.get("input"), dict) else ""
    
    # Only intercept Bash tool
    if name != "Bash":
        return json.dumps({"is_allowed": True})
    
    # Check against blocklist
    for pattern, reason in BLOCKLIST_PATTERNS:
        if re.search(pattern, cmd):
            _log_block(cmd, reason)
            return json.dumps({
                "is_allowed": False,
                "error": f"⛔ **Blocked by pre-tool-use hook**: {reason}\n\n"
                         f"If this was intentional, use the exact command in a terminal "
                         f"session or add an exception by prefixing with `#allow`.",
            })
    
    return json.dumps({"is_allowed": True})


def _log_block(cmd: str, reason: str):
    """Log a blocked command attempt to the log file."""
    try:
        log_dir = os.path.dirname(LOG_FILE)
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        project = os.getcwd()
        log_line = f"[{timestamp}] REASON={reason} | PROJECT={project} | CMD={cmd[:200]}\n"
        
        with open(LOG_FILE, "a") as f:
            f.write(log_line)
    except Exception:
        pass  # Silently fail — we don't want logging to break the hook


if __name__ == "__main__":
    result = main()
    print(result)
