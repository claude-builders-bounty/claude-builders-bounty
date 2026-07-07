#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Hook — Block destructive bash commands.

Installation:
    mkdir -p ~/.claude/hooks/
    cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
    chmod +x ~/.claude/hooks/pre-tool-use.py

    Then add to your Claude Code config:
    {
      "hooks": {
        "pre-tool-use": ["python3 ~/.claude/hooks/pre-tool-use.py"]
      }
    }

This hook intercepts bash commands before execution and blocks patterns
that could cause irreversible damage. Every blocked attempt is logged.
"""

import sys
import json
import re
import os
from datetime import datetime, timezone

# ── Configuration ────────────────────────────────────────────
LOG_DIR = os.path.expanduser("~/.claude/hooks")
LOG_FILE = os.path.join(LOG_DIR, "blocked.log")

# Patterns that will be BLOCKED
# Each pattern is a (regex, explanation) tuple
BLOCKED_PATTERNS = [
    # Destructive filesystem operations
    (r"\brm\s+-rf\b", "rm -rf (recursive force delete)"),
    (r"\brm\s+-r\b", "rm -r (recursive delete)"),
    (r"\brm\s+.*--no-preserve-root\b", "rm targeting root directory"),

    # Force push and destructive git operations
    (r"\bgit\s+push\s+.*--force\b", "git push --force"),
    (r"\bgit\s+push\s+.*-f\b", "git push -f (force push)"),
    (r"\bgit\s+reset\s+--hard\b", "git reset --hard (destroys working tree)"),
    (r"\bgit\s+clean\s+-fdx\b", "git clean -fdx (removes all untracked files)"),

    # Database destruction
    (r"\bDROP\s+TABLE\b", "DROP TABLE (database table destruction)"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE (database destruction)"),
    (r"\bTRUNCATE\b", "TRUNCATE (removes all rows)"),
    (r"\bDELETE\s+FROM\b(?!.*\bWHERE\b)", "DELETE FROM without WHERE clause"),
    (r"\bDELETE\s+FROM\s+\w+\s*;", "DELETE FROM without WHERE clause"),

    # System-level dangerous commands
    (r"\bchmod\s+777\b", "chmod 777 (world-writable permissions)"),
    (r"\bchmod\s+-R\s+777\b", "chmod -R 777 (recursive world-writable)"),
    (r"\b>\/dev\/sd[a-z]\b", "Writing directly to block device"),
    (r"\bdd\s+if=.*of=\/dev\/", "dd writing to block device"),
    (r"\bmkfs\.", "mkfs (filesystem creation/destruction)"),
    (r"\b:\s*\(\)\s*\{\s*:\s*\|\:", "Fork bomb pattern detected"),

    # Environment destruction
    (r"\brm\s+.*~\/\.ssh\b", "Deleting SSH keys"),
    (r"\brm\s+.*~\/\.gnupg\b", "Deleting GPG keys"),
    (r"\brm\s+.*\/\.git\b", "Deleting .git directory"),

    # Dangerous pipes and redirects
    (r"\|\s*sh\b", "Piping content directly to shell interpreter"),
    (r"\bcurl\s+.*\|\s*bash\b", "curl piped to bash (remote code execution)"),
    (r"\bwget\s+.*-O\s*-\s*\|\s*sh\b", "wget piped to shell"),
]


def log_blocked(command, project_path, patterns_matched):
    """Log a blocked attempt to the log file."""
    os.makedirs(LOG_DIR, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "project_path": project_path,
        "patterns_matched": [p[1] for p in patterns_matched],
    }

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def check_command(command):
    """Check a command against blocked patterns. Returns list of matches."""
    matches = []
    for pattern, explanation in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            matches.append((pattern, explanation))
    return matches


def main():
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        # No input or invalid — allow
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    project_path = input_data.get("cwd", "")

    # Only intercept bash/shell commands
    if tool_name not in ("bash", "shell_executor", "execute_command", "Bash"):
        sys.exit(0)

    # Extract the command
    command = tool_input.get("command", "") or tool_input.get("cmd", "") or ""
    if not command:
        sys.exit(0)

    # Check against blocked patterns
    matches = check_command(command)

    if matches:
        # Log the blocked attempt
        log_blocked(command, project_path, matches)

        # Build clear error message
        reasons = "\n".join(f"  • {explanation}" for _, explanation in matches)
        error_msg = f"""
╔══════════════════════════════════════════════════════════════╗
║  BLOCKED: Destructive command intercepted                    ║
╠══════════════════════════════════════════════════════════════╣
║  Command: {command[:60]}
║
║  Reason(s):
{reasons}
║
║  This command was blocked to prevent irreversible damage.
║  If you are certain this is safe, bypass the hook manually
║  or add an exception to the hook configuration.
║
║  Logged to: {LOG_FILE}
╚══════════════════════════════════════════════════════════════╝
"""
        print(error_msg, file=sys.stderr)
        sys.exit(1)  # Block execution

    # No matches — allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
