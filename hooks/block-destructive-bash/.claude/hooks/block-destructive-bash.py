#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Reads JSON from stdin (Claude Code hook protocol), inspects bash commands
for dangerous patterns, and blocks them with a clear explanation.

Exit codes (Claude Code hook protocol):
  0 — allow the tool call
  2 — block the tool call (stderr is shown to the agent)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Destructive patterns — each tuple is (compiled_regex, human-readable label)
# ---------------------------------------------------------------------------
DESTRUCTIVE_PATTERNS = [
    # Recursive force-delete (files, dirs, home, root)
    (re.compile(r'\brm\s+(-[a-zA-Z]*f[a-zA-Z]*\s+|-[a-zA-Z]*r[a-zA-Z]*\s+){0,}(-[a-zA-Z]*[rRf]\w*\s+){0,}(-rf|-fr|-r\s+-f|-f\s+-r)\b', re.I),
     "recursive force-delete (rm -rf)"),
    (re.compile(r'\brm\s+(-[a-zA-Z]*[rR]\w*\s+).*?(/|~|\*)', re.I),
     "recursive delete with path"),

    # DROP / TRUNCATE / DELETE without WHERE (SQL)
    (re.compile(r'\bDROP\s+(TABLE|DATABASE|INDEX|VIEW|SCHEMA)\b', re.I),
     "SQL DROP statement"),
    (re.compile(r'\bTRUNCATE\s+(TABLE\s+)?', re.I),
     "SQL TRUNCATE statement"),
    (re.compile(r'\bDELETE\s+FROM\s+\S+\s*(;|$)', re.I),
     "SQL DELETE without WHERE clause"),

    # Destructive git operations
    (re.compile(r'\bgit\s+push\s+.*--force\b', re.I),
     "force push (--force)"),
    (re.compile(r'\bgit\s+push\s+.*-f\b', re.I),
     "force push (-f)"),
    (re.compile(r'\bgit\s+reset\s+--hard\b', re.I),
     "hard reset"),
    (re.compile(r'\bgit\s+clean\s+.*-f\b', re.I),
     "forced clean"),
    (re.compile(r'\bgit\s+branch\s+.*-D\b', re.I),
     "force-delete branch"),

    # Dangerous filesystem operations
    (re.compile(r'\bmkfs\b', re.I),
     "filesystem creation (mkfs)"),
    (re.compile(r'\bdd\s+.*of=/dev/', re.I),
     "raw disk write (dd to device)"),
    (re.compile(r'\bchmod\s+(-R\s+)?777\b', re.I),
     "world-writable permissions (chmod 777)"),
    (re.compile(r'\bchown\s+.*-R\b', re.I),
     "recursive ownership change"),

    # Fork bombs & process abuse
    (re.compile(r':\(\)\s*\{.*:\|:', re.I),
     "fork bomb"),

    # curl/wget piped to shell
    (re.compile(r'(curl|wget)\s+.*\|\s*(bash|sh|zsh|dash)\b', re.I),
     "piping remote script to shell"),
]


def log_blocked(command: str, project_path: str) -> None:
    """Append a blocked-attempt entry to ~/.claude/hooks/blocked.log."""
    log_dir = os.path.expanduser("~/.claude/hooks")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "blocked.log")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] BLOCKED | project={project_path} | command={command}\n"

    with open(log_path, "a") as f:
        f.write(entry)


def check_command(command: str) -> str | None:
    """Return a description if the command matches a destructive pattern, else None."""
    for pattern, label in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return label
    return None


def main() -> None:
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        # Can't parse input — let it through rather than break workflow
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Only intercept bash/shell commands
    if tool_name.lower() not in ("bash", "bashcommand", "execute_command"):
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Allow safe patterns that LOOK dangerous but aren't
    # (e.g., grep for 'rm -rf' in documentation)
    safe_context = [
        re.compile(r'\bgrep\b', re.I),
        re.compile(r'\becho\b.*rm\b', re.I),
        re.compile(r'\bprintf\b.*rm\b', re.I),
        re.compile(r'#.*rm\b'),  # comments
        re.compile(r'\bsed\b.*rm\b', re.I),
    ]
    for safe in safe_context:
        if safe.search(command):
            sys.exit(0)

    reason = check_command(command)
    if reason:
        project_path = data.get("cwd", os.getcwd())
        log_blocked(command, project_path)

        print(
            f"⛔ Command blocked by safety hook.\n"
            f"Reason: {reason}\n"
            f"Command: {command}\n\n"
            f"This operation is destructive and has been prevented.\n"
            f"If you truly need to run this, ask the user to approve it or\n"
            f"temporarily disable the hook in .claude/settings.json.",
            file=sys.stderr,
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
