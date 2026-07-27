#!/usr/bin/env python3
"""Claude Code pre-tool-use hook — blocks destructive bash commands.

Install: copy to ~/.claude/hooks/pre_tool_use and chmod +x
Format follows Claude Code hooks specification.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

LOG_FILE = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns that are ALWAYS blocked
DANGEROUS_PATTERNS = [
    # Filesystem destruction
    (r"\brm\s+-rf\b", "rm -rf (recursive force delete)"),
    (r"\brm\s+-r\s+-f\b", "rm -r -f (recursive force delete)"),
    (r"\brm\s+.*--no-preserve-root\b", "rm --no-preserve-root"),
    # Force push to main/master
    (r"git\s+push\s+.*(--force|--force-with-lease)\b.*\b(main|master)\b",
     "git push --force to main/master"),
    # Database destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE"),
    (r"\bTRUNCATE\s+(TABLE\s+)?\w+", "TRUNCATE TABLE"),
    (r"\bDELETE\s+FROM\s+\w+\s*(?!.*WHERE\b)", "DELETE FROM without WHERE clause"),
    # Dangerous chmod/chown
    (r"\bchmod\s+(-R\s+)?777\b", "chmod 777 (world-writable)"),
    (r"\bchown\s+-R\s+.*\s+/\b", "chown -R on root directory"),
    # Fork bomb prevention
    (r":\(\)\s*\{", "fork bomb pattern"),
    # Write to block devices
    (r"\bdd\s+.*of=/dev/sd", "dd writing to block device"),
    # Dangerous format/wiping
    (r"\bmkfs\.", "mkfs (filesystem format)"),
    (r"\bwipefs\b", "wipefs (wipe filesystem signatures)"),
]

# Patterns that trigger a WARNING but are NOT blocked
WARNING_PATTERNS = [
    (r"git\s+push\s+.*--force", "git push --force (non-main branch)"),
    (r"\bsudo\s+rm\b", "sudo rm"),
    (r"\bcurl.*\|\s*(ba)?sh\b", "curl pipe to shell"),
    (r"\bwget.*\|\s*(ba)?sh\b", "wget pipe to shell"),
]


def log_block(command: str, pattern_desc: str, project_path: str, blocked: bool) -> None:
    """Log blocked/warned commands to the log file."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command[:500],
        "pattern": pattern_desc,
        "project_path": project_path,
        "action": "BLOCKED" if blocked else "WARNED",
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command: str, project_path: str) -> dict:
    """Check a command against dangerous patterns."""
    # Check BLOCK patterns first
    for pattern, desc in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_block(command, desc, project_path, blocked=True)
            return {
                "continue": False,
                "reason": (
                    f"BLOCKED: {desc}\n\n"
                    f"This command matches a destructive pattern and was blocked "
                    f"by the pre-tool-use safety hook.\n\n"
                    f"Command: {command[:200]}\n"
                    f"Pattern: {desc}\n\n"
                    f"If you are ABSOLUTELY certain this is safe, you can:\n"
                    f"1. Use a safer alternative (e.g., 'rm -i' instead of 'rm -rf')\n"
                    f"2. Temporarily disable the hook: mv ~/.claude/hooks/pre_tool_use ~/.claude/hooks/pre_tool_use.disabled\n"
                    f"3. Run the command manually in a separate terminal"
                ),
            }

    # Check WARNING patterns
    for pattern, desc in WARNING_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_block(command, desc, project_path, blocked=False)
            return {
                "continue": True,
                "warning": (
                    f"WARNING: {desc}\n\n"
                    f"This command looks potentially risky but will proceed.\n"
                    f"Command: {command[:200]}\n"
                    f"Pattern: {desc}"
                ),
            }

    # Safe command
    return {"continue": True}


def main():
    """Main hook entry point — reads tool call from stdin, checks it."""
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If we can't parse the input, allow it through
        print(json.dumps({"continue": True}))
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only intercept bash/terminal commands
    if tool_name not in ("bash", "Bash", "terminal"):
        print(json.dumps({"continue": True}))
        return 0

    command = tool_input.get("command", "")
    if not command:
        print(json.dumps({"continue": True}))
        return 0

    project_path = os.getcwd()

    result = check_command(command, project_path)
    print(json.dumps(result))
    return 0 if result.get("continue", True) else 1


if __name__ == "__main__":
    sys.exit(main())
