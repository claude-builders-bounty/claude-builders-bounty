#!/usr/bin/env python3
"""
Pre-tool-use hook for Claude Code that blocks destructive bash commands.

Install: place this file in ~/.claude/hooks/pre_tool_use.py and configure
~/.claude/settings.json:
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/pre_tool_use.py"
      }]
    }]
  }
}

Input: Claude Code passes a JSON event on stdin with {'tool_input': {'command': '...'}}.
We exit non-zero to block, printing a clear reason to stderr.
We exit 0 to allow.
All blocked attempts are logged to ~/.claude/hooks/blocked.log.
"""
import sys
import os
import json
import re
import datetime

LOG_PATH = os.path.expanduser("~/.claude/hooks/blocked.log")

# Patterns of destructive commands we block.
# Each is a compiled regex; a match means block.
BLOCK_PATTERNS = [
    (r"\brm\s+(-[a-zA-Z]*r|-[a-zA-Z]*f|-[a-zA-Z]*rf|-rf|-fr)\b", "rm -rf (force recursive delete)"),
    (r"\brm\s+(-[a-zA-Z]*f|-[a-zA-Z]*rf|-[a-zA-Z]*fr)\b", "rm -f (force delete)"),
    (r"\bdrop\s+table\b", "DROP TABLE"),
    (r"\btruncate\b", "TRUNCATE"),
    (r"\bgit\s+push\s+(--force|-f)\b", "git push --force"),
    (r"\bgit\s+push\s+\S+\s+\S+\s+--force\b", "git push --force (with ref)"),
    (r"\bdelete\s+from\b\s+\w+\s*(;|$)", "DELETE FROM without WHERE clause"),
    (r"\bdelete\s+from\b\s+\w+\s+where\b", "DELETE FROM (allowed - has WHERE)"),
]

# Compiled patterns that block (everything except the last which is allowed)
BLOCK_RE = [
    (re.compile(p, re.IGNORECASE), reason)
    for p, reason in BLOCK_PATTERNS
    if "allowed" not in reason
]


def log_block(command, reason, project_path=""):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    ts = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{ts} | BLOCKED: {reason} | CMD: {command} | PROJECT: {project_path}\n")


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        # If we can't parse input, allow (fail open for non-destructive safety).
        sys.exit(0)

    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    # Try to derive project path from environment / cwd
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

    for pattern, reason in BLOCK_RE:
        if pattern.search(command):
            log_block(command, reason, project_path)
            sys.stderr.write(
                f"\n🛑 BLOCKED: {reason}\n"
                f"   Command: {command}\n"
                f"   This destructive operation was prevented by the pre-tool-use hook.\n"
                f"   Logged to {LOG_PATH}\n"
            )
            sys.exit(2)  # non-zero exit blocks the tool call

    sys.exit(0)  # allow


if __name__ == "__main__":
    main()
