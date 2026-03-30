#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook: blocks destructive bash commands.

Install: place in ~/.claude/hooks/pre_tool_use_hook.py
Configure in ~/.claude/settings.json (see README).

Input:  JSON on stdin  { "tool_name": "...", "tool_input": { "command": "..." } }
Output: JSON on stdout { "continue": true/false, "reason": "..." }
Exit 0 always — we communicate via JSON, not exit codes.
"""

import json
import sys
import os
import re
import logging
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = [
    # Pattern                   Human-readable description
    (r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b',           'rm -rf (recursive force delete)'),
    (r'\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b',           'rm -fr (recursive force delete)'),
    (r'\bDROP\s+TABLE\b',                           'DROP TABLE (destructive SQL)'),
    (r'\bTRUNCATE\b',                               'TRUNCATE (destructive SQL)'),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)',          'DELETE FROM without WHERE clause'),
    (r'\bgit\s+push\s+.*--force\b',                'git push --force'),
    (r'\bgit\s+push\s+.*-f\b',                     'git push -f (force push)'),
    (r'\bgit\s+push\s+--force-with-lease\b',       'git push --force-with-lease'),
]

HOOK_DIR   = Path.home() / ".claude" / "hooks"
LOG_FILE   = HOOK_DIR / "blocked.log"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logger() -> logging.Logger:
    HOOK_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("claude_hook")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(message)s",
                              datefmt="%Y-%m-%dT%H:%M:%S")
        )
        logger.addHandler(handler)
    return logger

# ---------------------------------------------------------------------------
# Detection logic
# ---------------------------------------------------------------------------

def find_match(command: str) -> tuple[str, str] | None:
    """Return (pattern_description, matched_text) if a dangerous pattern is found."""
    for pattern, description in BLOCKED_PATTERNS:
        match = re.search(pattern, command, re.IGNORECASE | re.DOTALL)
        if match:
            return description, match.group(0)
    return None

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger = setup_logger()

    # Read hook input from stdin
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except Exception as e:
        # If we can't parse, let it pass through — don't block due to hook errors
        print(json.dumps({"continue": True}))
        return

    tool_name  = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # We only care about Bash / shell tool calls
    if tool_name not in ("Bash", "bash", "shell", "run_bash", "computer"):
        print(json.dumps({"continue": True}))
        return

    command = tool_input.get("command", "") or tool_input.get("cmd", "")

    if not command:
        print(json.dumps({"continue": True}))
        return

    result = find_match(command)

    if result is None:
        print(json.dumps({"continue": True}))
        return

    # --- Destructive command detected ---
    description, matched_text = result
    project_path = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    timestamp    = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    log_line = (
        f"BLOCKED | timestamp={timestamp} | "
        f"pattern={description!r} | "
        f"matched={matched_text!r} | "
        f"project={project_path} | "
        f"command={command!r}"
    )
    logger.warning(log_line)

    reason = (
        f"BLOCKED by safety hook: detected \"{description}\".\n\n"
        f"Matched text: `{matched_text}`\n\n"
        f"This command was intercepted because it is potentially irreversible and "
        f"could cause data loss. If you genuinely need to run this command, please "
        f"confirm explicitly by stating the full intent, or run it manually outside "
        f"of Claude Code.\n\n"
        f"Blocked attempt logged to: {LOG_FILE}"
    )

    print(json.dumps({
        "continue": False,
        "reason": reason
    }))


if __name__ == "__main__":
    main()
