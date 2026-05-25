#!/usr/bin/env python3
"""pre-tool-use hook for Claude Code — blocks destructive bash commands.

Installation:
  mkdir -p ~/.claude/hooks
  cp block_destructive.sh ~/.claude/hooks/pre_tool_use
  chmod +x ~/.claude/hooks/pre_tool_use

The hook intercepts every bash command before execution and blocks
dangerous patterns like rm -rf, DROP TABLE, git push --force, etc.
Blocked attempts are logged to ~/.claude/hooks/blocked.log
"""

import json
import os
import re
import sys
from datetime import datetime

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")
HOOK_NAME = "block-destructive"

# Patterns that are ALWAYS blocked (destructive)
DESTRUCTIVE_PATTERNS = [
    # File system destruction
    (r'\brm\s+-[rR]f\b', "Recursive force delete — use `rm` with explicit paths only"),
    (r'\brm\s+-[rR]\s+/', "Recursive delete from root — corrupts the system"),
    (r'\bmv\s+/\s+', "Moving root directory — corrupts the filesystem"),
    (r'\bchmod\s+-R\s+0{3}\b', "Recursive permission removal — breaks access"),
    (r'\bchown\s+-R\b', "Recursive ownership change — risky in production"),
    (r'\bdd\s+if=/dev/zero\b', "Zero-fill — destructive to disk"),
    (r'\bmkfs|\bmkswap\b', "Filesystem creation — destroys existing data"),
    
    # Database destruction
    (r'\bDROP\s+(TABLE|DATABASE|SCHEMA|INDEX|VIEW|FUNCTION|PROCEDURE)\b', 
     "Destructive SQL — removes database objects permanently"),
    (r'\bTRUNCATE\b', "Table truncation — removes all rows without backup"),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "Unconditional DELETE — missing WHERE clause removes all rows"),
    (r'\bUPDATE\s+\w+\s+SET\b(?!.*\bWHERE\b)', "Unconditional UPDATE — missing WHERE clause modifies all rows"),
    (r'\bALTER\s+TABLE.*\bDROP\b', "ALTER TABLE DROP — removes columns/tables"),
    
    # Git destruction
    (r'\bgit\s+push\s+--force\b', "Force push — overwrites remote history"),
    (r'\bgit\s+push\s+-f\b', "Force push (short flag) — overwrites remote history"),
    (r'\bgit\s+reset\s+--hard\b', "Hard reset — discards uncommitted changes permanently"),
    (r'\bgit\s+clean\s+-[fF][d]?[x]?\b', "Force clean — removes untracked files permanently"),
    (r'\bgit\s+rebase\s+--interactive\b', "Interactive rebase — rewrites commit history"),
    
    # System commands
    (r'\bshutdown\b', "System shutdown — interrupts all running processes"),
    (r'\breboot\b', "System reboot — interrupts all running processes"),
    (r'\binit\s+0\b|\binit\s+6\b', "System runlevel change — shuts down or reboots"),
    (r'\bpoweroff\b', "Power off — shuts down the system"),
    (r'\bhalt\b', "System halt — stops all CPUs"),
    
    # Production deployment safety
    (r'\bkubectl\s+delete\s+namespace\b', "Kubernetes namespace deletion — destroys all resources"),
    (r'\bdocker\s+(rm|system\s+prune)\s+-[f]\b', "Docker force removal — removes containers/images"),
    (r'\bterraform\s+destroy\b', "Terraform destroy — deletes all infrastructure"),
]

# Patterns that are ALLOWED with context (not blocked but logged)
MONITORED_PATTERNS = [
    r'\brm\b(?!\s+-[rR]f)',
    r'\bkill\b',
    r'\bsudo\b',
    r'\bwget|\bcurl\s+.*\|\s*(bash|sh)\b',
    r'\bchmod\s+7',
    r'\b>\s*/dev/',
]


def log_blocked(command: str, pattern_name: str, reason: str) -> None:
    """Log blocked command to the log file with timestamp."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    project = os.environ.get("CLAUDE_PROJECT", os.getcwd())
    entry = json.dumps({
        "timestamp": timestamp,
        "project": project,
        "command": command,
        "matched_pattern": pattern_name,
        "reason": reason,
    })
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")


def check_destructive(command: str) -> tuple[bool, str]:
    """Check if a command matches any destructive pattern.
    
    Returns: (is_blocked, reason)
    """
    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def main() -> None:
    """Main hook entrypoint."""
    try:
        input_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Not a JSON input — allow through
        json.dump({"status": "ok"}, sys.stdout)
        return

    # Extract the tool call
    tool_call = input_data.get("toolCall", {})
    tool_name = tool_call.get("tool", {}).get("name", "")
    
    # Only intercept bash tool
    if tool_name not in ("Bash", "bash", "execute_command"):
        json.dump({"status": "ok"}, sys.stdout)
        return

    # Extract the command
    command = ""
    for arg_name in ("command", "cmd", "code"):
        arg = tool_call.get("tool", {}).get("input", {}).get(arg_name, "")
        if arg:
            command = arg
            break

    if not command:
        json.dump({"status": "ok"}, sys.stdout)
        return

    # Check against destructive patterns
    is_blocked, reason = check_destructive(command)
    if is_blocked:
        log_blocked(command, "destructive", reason)
        result = {
            "status": "error",
            "message": (
                f"⛔ **Command blocked by {HOOK_NAME} hook**\n\n"
                f"**Reason:** {reason}\n\n"
                f"**Command:** `{command[:200]}`\n\n"
                f"Logged to `{LOG_FILE}`. If you need to run this command, "
                f"temporarily disable the hook with:\n"
                f"```bash\n"
                f"mv ~/.claude/hooks/pre_tool_use ~/.claude/hooks/pre_tool_use.disabled\n"
                f"```"
            ),
        }
    else:
        # Allow safe commands through
        result = {"status": "ok"}

    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
