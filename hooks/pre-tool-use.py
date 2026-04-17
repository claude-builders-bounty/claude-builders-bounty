#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: Block destructive bash commands

Install:
  cp pre-tool-use.py ~/.claude/hooks/
  chmod +x ~/.claude/hooks/pre-tool-use.py

The hook will block dangerous commands and log them to ~/.claude/hooks/blocked.log
"""
import os
import sys
import re
import json
import logging
from datetime import datetime
from pathlib import Path

# Configuration
HOOKS_DIR = Path.home() / ".claude" / "hooks"
BLOCKED_LOG = HOOKS_DIR / "blocked.log"

# Dangerous patterns - must be matched carefully to avoid false positives
DANGEROUS_PATTERNS = [
    # Recursive force remove (but not --no-preserve-root which is rarely used)
    (r'\brm\s+-rf\s+/(?!.*--no-preserve-root)', "rm -rf /", "Recursive deletion of root directory"),
    (r'\brm\s+-rf\s+\$HOME(?!\S)', "rm -rf $HOME", "Recursive deletion of home directory"),
    (r'\brm\s+-rf\s+/tmp(?!\S)', "rm -rf /tmp", "Recursive deletion of /tmp"),
    (r'\brm\s+-rf\s+/var(?!\S)', "rm -rf /var", "Recursive deletion of /var"),
    (r'\brm\s+-rf\s+/usr(?!\S)', "rm -rf /usr", "Recursive deletion of /usr"),
    (r'\brm\s+-rf\s+/bin(?!\S)', "rm -rf /bin", "Recursive deletion of /bin"),
    (r'\brm\s+-rf\s+/lib(?!\S)', "rm -rf /lib", "Recursive deletion of /lib"),
    
    # SQL destructive commands
    (r'\bDROP\s+TABLE\b', "DROP TABLE", "SQL DROP TABLE command"),
    (r'\bDROP\s+DATABASE\b', "DROP DATABASE", "SQL DROP DATABASE command"),
    (r'\bDROP\s+INDEX\b', "DROP INDEX", "SQL DROP INDEX command"),
    (r'\bTRUNCATE\b', "TRUNCATE", "SQL TRUNCATE command"),
    
    # Git force push (can overwrite history)
    (r'\bgit\s+push\s+.*--force\b', "git push --force", "Git force push (overwrites remote history)"),
    (r'\bgit\s+push\s+.*-f\b', "git push -f", "Git force push shorthand"),
    
    # Dangerous file operations
    (r'>\s*/dev/sd[a-z]', "> /dev/sdX", "Direct write to disk device"),
    (r'dd\s+.*of=/dev/', "dd to block device", "Direct block device write"),
    
    # DELETE without WHERE (accidental data loss)
    # Only block if there's a table name but no WHERE
    (r'\bDELETE\s+FROM\s+\w+\s*;?\s*$', "DELETE without WHERE", "SQL DELETE without WHERE clause"),
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger("pre-tool-use")


def log_blocked(command: str, reason: str, project_path: str = ""):
    """Log blocked command to blocked.log"""
    try:
        HOOKS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().isoformat()()
        project = project_path or os.environ.get("CLAUDE_PROJECT_PATH", "unknown")
        
        with open(BLOCKED_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] BLOCKED: {command}\n")
            f.write(f"  Reason: {reason}\n")
            f.write(f"  Project: {project}\n")
            f.write("-" * 60 + "\n")
    except Exception as e:
        logger.warning(f"Failed to write to blocked.log: {e}")


def check_command(command: str) -> tuple:
    """
    Check if a command should be blocked.
    Returns (blocked, reason)
    """
    for pattern, name, reason in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, f"{reason} ({name})"
    return False, ""


def get_tool_name() -> str:
    """Get the tool name from Claude's hook input"""
    try:
        # Claude Code passes tool name as first argument
        return sys.argv[1] if len(sys.argv) > 1 else "unknown"
    except Exception:
        return "unknown"


def get_tool_input() -> dict:
    """Get the tool input from Claude's hook input"""
    try:
        # Read JSON from stdin (Claude Code passes hook data via stdin)
        if not sys.stdin.isatty():
            data = json.loads(sys.stdin.read())
            return data
    except Exception:
        pass
    return {}


def main():
    """Main hook entry point"""
    tool_name = get_tool_name()
    
    # Only check bash commands
    if tool_name != "bash":
        sys.exit(0)  # Allow all non-bash tools
    
    tool_input = get_tool_input()
    command = tool_input.get("command", "")
    
    if not command:
        sys.exit(0)  # Allow empty commands
    
    blocked, reason = check_command(command)
    
    if blocked:
        # Log the blocked attempt
        log_blocked(command, reason)
        
        # Print error message to stderr (visible to Claude)
        print("=" * 60, file=sys.stderr)
        print("DANGEROUS COMMAND BLOCKED", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(f"\n  Command: {command}", file=sys.stderr)
        print(f"  Reason: {reason}", file=sys.stderr)
        print(f"  Log: {BLOCKED_LOG}", file=sys.stderr)
        print("\n  If this command is legitimate, you can:", file=sys.stderr)
        print("  1. Break it into smaller, safe commands", file=sys.stderr)
        print("  2. Add specific paths to exclude", file=sys.stderr)
        print("  3. Temporarily disable the hook in ~/.claude/hooks/", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        
        # Exit with error code to block the command
        sys.exit(1)
    
    # Allow the command
    sys.exit(0)


if __name__ == "__main__":
    main()
