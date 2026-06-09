#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block destructive bash commands.

Intercepts bash commands before execution and blocks dangerous patterns.
Logs every blocked attempt to ~/.claude/hooks/blocked.log.

Installation:
    mkdir -p ~/.claude/hooks
    cp pre_tool_use_hook.py ~/.claude/hooks/pre_tool_use_hook.py
    chmod +x ~/.claude/hooks/pre_tool_use_hook.py

Configuration via ~/.claude/hooks/config.json (optional):
    {
      "extra_patterns": ["custom_pattern1", "custom_pattern2"],
      "allow_patterns": ["rm -rf /tmp/my_safe_dir"],
      "log_file": "~/.claude/hooks/blocked.log"
    }
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Dangerous patterns ───────────────────────────────────────────────────────

BLOCKED_PATTERNS = [
    # rm -rf (any path, but allow common safe dirs)
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "rm -rf: Recursive forced deletion"),
    (r"\brm\s+(-[a-zA-Z]*f[a-zA-Z]*r|-[a-zA-Z]*r[a-zA-Z]*f)\s", "rm -rf: Recursive forced deletion"),

    # DROP TABLE / DROP DATABASE
    (r"\bDROP\s+TABLE\b", "DROP TABLE: Destructive SQL operation"),
    (r"\bDROP\s+DATABASE\b", "DROP DATABASE: Destructive SQL operation"),

    # TRUNCATE
    (r"\bTRUNCATE\s+TABLE\b", "TRUNCATE TABLE: Destructive SQL operation"),
    (r"\bTRUNCATE\b", "TRUNCATE: Destructive SQL operation"),

    # DELETE FROM without WHERE clause
    (r"\bDELETE\s+FROM\b(?![\s\S]*\bWHERE\b)", "DELETE FROM without WHERE: Deletes all rows"),

    # git push --force (but allow --force-with-lease)
    (r"\bgit\s+push\b.*--force(?!-with-lease)", "git push --force: Force push overwrites history"),
    (r"\bgit\s+push\b.*-f\b(?![-l])", "git push -f: Force push overwrites history"),

    # Additional dangerous patterns
    (r"\bmkfs\b", "mkfs: Formats filesystem"),
    (r"\bdd\s+.*of=/dev/", "dd to device: Can overwrite disks"),
    (r":(){ :\|:& };:", "Fork bomb: Crash system"),
    (r"\bcurl\b.*\|\s*(ba)?sh", "curl pipe to shell: Remote code execution"),
    (r"\bwget\b.*\|\s*(ba)?sh", "wget pipe to shell: Remote code execution"),
    (r"\bchmod\s+-R\s+777\b", "chmod 777 -R: Insecure permissions"),
    (r"\bchown\s+-R\b.*root", "chown -R root: Changes ownership to root"),
]

# ─── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load optional config from ~/.claude/hooks/config.json."""
    config_path = Path.home() / ".claude" / "hooks" / "config.json"
    if config_path.exists():
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_log_path(config: dict) -> Path:
    """Get log file path from config or default."""
    log_file = config.get("log_file", "~/.claude/hooks/blocked.log")
    return Path(log_file).expanduser()


# ─── Logging ──────────────────────────────────────────────────────────────────

def log_blocked_attempt(command: str, reason: str, log_path: Path) -> None:
    """Log a blocked command attempt."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    project_path = os.getcwd()

    entry = (
        f"[{timestamp}] BLOCKED\n"
        f"  Command: {command}\n"
        f"  Reason:  {reason}\n"
        f"  Project: {project_path}\n"
        f"{'─' * 60}\n"
    )

    with open(log_path, "a") as f:
        f.write(entry)


# ─── Pattern matching ─────────────────────────────────────────────────────────

def check_command(command: str, config: dict) -> str | None:
    """
    Check command against blocked patterns.
    Returns the reason if blocked, None if safe.
    """
    # Check allowlist first (safe overrides)
    for allowed in config.get("allow_patterns", []):
        if allowed in command:
            return None

    # Get all patterns (built-in + extra)
    patterns = list(BLOCKED_PATTERNS)
    for extra in config.get("extra_patterns", []):
        patterns.append((extra, f"Custom pattern: {extra}"))

    # Check each pattern
    for pattern, reason in patterns:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return reason
        except re.error:
            # Invalid regex, skip
            if pattern.lower() in command.lower():
                return reason

    return None


# ─── Main hook ────────────────────────────────────────────────────────────────

def main() -> None:
    """
    Claude Code PreToolUse hook entry point.

    Reads tool input from stdin (JSON), checks if the bash command is safe,
    and outputs a JSON response.

    Input format (from Claude Code):
    {
      "tool": "bash",
      "input": {
        "command": "rm -rf /"
      }
    }

    Output format:
    {
      "decision": "block",
      "reason": "..."
    }
    or
    {
      "decision": "allow"
    }
    """
    # Read input from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            # No input, allow
            print(json.dumps({"decision": "allow"}))
            return
        data = json.loads(raw_input)
    except (json.JSONDecodeError, Exception):
        # Can't parse, allow (fail open for non-bash tools)
        print(json.dumps({"decision": "allow"}))
        return

    # Only intercept bash/bash-like tools
    tool_name = data.get("tool", "")
    if tool_name not in ("bash", "Bash", "terminal", "shell"):
        print(json.dumps({"decision": "allow"}))
        return

    # Extract command
    tool_input = data.get("input", {})
    command = tool_input.get("command", "")

    if not command:
        print(json.dumps({"decision": "allow"}))
        return

    # Load config and check
    config = load_config()
    log_path = get_log_path(config)
    reason = check_command(command, config)

    if reason:
        # Block the command
        log_blocked_attempt(command, reason, log_path)

        response = {
            "decision": "block",
            "reason": (
                f"🚫 Command blocked by safety hook.\n"
                f"Reason: {reason}\n"
                f"Attempted command: `{command}`\n"
                f"This command was logged to {log_path}\n"
                f"If this is intentional, add it to allow_patterns in config.json."
            )
        }
        print(json.dumps(response))
    else:
        # Allow
        print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
