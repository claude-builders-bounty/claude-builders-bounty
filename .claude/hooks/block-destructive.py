#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook — Block Destructive Bash Commands

Intercepts Bash tool calls before execution and blocks dangerous patterns
such as rm -rf, DROP TABLE, git push --force, TRUNCATE, and unqualified DELETEs.

Reads the tool-call JSON from stdin (Claude Code hook protocol).
Outputs a permission decision to stdout (JSON).
Logs blocked attempts to ~/.claude/hooks/blocked.log.

Configuration: rules are loaded from rules.json alongside this script.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

HOOK_DIR = Path(__file__).resolve().parent
LOG_FILE = HOOK_DIR / "blocked.log"
RULES_FILE = HOOK_DIR / "rules.json"


# ---------------------------------------------------------------------------
# Default destructive patterns
# ---------------------------------------------------------------------------

DEFAULT_PATTERNS: list[dict[str, str]] = [
    # Filesystem destruction
    {
        "name": "rm-recursive-force",
        "pattern": r"\brm\s+.*(-r\s+-f|-rf\s|--recursive.*--force)",
        "description": "Recursive forced removal (rm -rf / equivalent)",
    },
    {
        "name": "rm-root-recursive",
        "pattern": r"\brm\s+.*-r[^\w].*/\s",
        "description": "Recursive removal targeting root or absolute path",
    },
    {
        "name": "chmod-777",
        "pattern": r"\bchmod\s+.*777\b",
        "description": "World-writable permissions (chmod 777)",
    },
    {
        "name": "chmod-recursive-777",
        "pattern": r"\bchmod\s+.*-R.*777\b",
        "description": "Recursive world-writable permissions",
    },
    {
        "name": "mkfs",
        "pattern": r"\bmkfs\.?\w*\s",
        "description": "Filesystem creation (mkfs.*)",
    },
    {
        "name": "dd-overwrite",
        "pattern": r"\bdd\s+if=.*of=/dev/\w",
        "description": "Raw device overwrite with dd",
    },
    {
        "name": "redirect-root-device",
        "pattern": r">\s*/dev/sd[a-z]\b",
        "description": "Redirect to block device",
    },
    {
        "name": "fork-bomb",
        "pattern": r":\(\)\s*\{\s*:\s*\|\s*:?\s*&\s*\}\s*;?\s*:?",
        "description": "Fork bomb",
    },

    # Git force-push
    {
        "name": "git-push-force",
        "pattern": r"\bgit\s+push\s+.*(--force|--force-with-lease)\b",
        "description": "Git force push (rewrites remote history)",
    },
    {
        "name": "git-hard-reset-push",
        "pattern": r"\bgit\s+push\s+.*\+.*:",
        "description": "Git push with +ref (force push variant)",
    },

    # Database destruction
    {
        "name": "drop-table",
        "pattern": r"\bDROP\s+TABLE\b",
        "description": "DROP TABLE statement",
    },
    {
        "name": "drop-database",
        "pattern": r"\bDROP\s+DATABASE\b",
        "description": "DROP DATABASE statement",
    },
    {
        "name": "truncate-table",
        "pattern": r"\bTRUNCATE\s+(TABLE\s+)?\w",
        "description": "TRUNCATE TABLE statement",
    },
    {
        "name": "delete-without-where",
        "pattern": r"\bDELETE\s+FROM\s+\w+(?!.*\bWHERE\b)",
        "description": "DELETE FROM without WHERE clause (deletes all rows)",
    },
]


# ---------------------------------------------------------------------------
# Rules loading
# ---------------------------------------------------------------------------

def load_rules() -> dict[str, Any]:
    """Load rules from rules.json, falling back to defaults."""
    if RULES_FILE.exists():
        try:
            with open(RULES_FILE) as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError) as exc:
            log_event(
                "WARN",
                "Could not parse rules.json; using defaults",
                extra={"error": str(exc)},
            )
    return {}


def get_patterns(rules: dict[str, Any]) -> list[dict[str, str]]:
    """Merge user-defined patterns with defaults."""
    custom = rules.get("patterns", [])
    if custom:
        return custom
    return DEFAULT_PATTERNS


def get_allowed_commands(rules: dict[str, Any]) -> list[str]:
    """Commands that are always allowed (whitelist overrides)."""
    return rules.get("allowed_commands", [])


def get_require_confirmation(rules: dict[str, Any]) -> bool:
    """If True, ask user instead of outright denying."""
    return rules.get("require_confirmation", False)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_event(level: str, message: str, extra: dict[str, Any] | None = None) -> None:
    """Append a JSON log line to blocked.log."""
    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "message": message,
    }
    if extra:
        entry.update(extra)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        # Best-effort logging — never crash the hook on log failure
        pass


# ---------------------------------------------------------------------------
# Pattern matching
# ---------------------------------------------------------------------------

def check_command(
    command: str,
    patterns: list[dict[str, str]],
    allowed_commands: list[str],
) -> list[dict[str, str]]:
    """
    Return a list of matched patterns.
    Whitelisted commands always bypass checks.
    """
    # Check whitelist first
    for allowed in allowed_commands:
        if re.search(allowed, command):
            return []

    matched: list[dict[str, str]] = []
    for rule in patterns:
        try:
            if re.search(rule["pattern"], command, re.IGNORECASE):
                matched.append(rule)
        except re.error:
            log_event("WARN", f"Invalid regex pattern: {rule.get('name', '?')}")
    return matched


# ---------------------------------------------------------------------------
# Decision output
# ---------------------------------------------------------------------------

def allow() -> None:
    """Let the tool call proceed normally."""
    # Exit 0 with no hookSpecificOutput → normal permission flow
    sys.exit(0)


def deny(reason: str) -> None:
    """Block the tool call with a reason."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


def ask_user(reason: str) -> None:
    """Prompt the user for confirmation."""
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }
    json.dump(output, sys.stdout)
    sys.exit(0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    # 1. Parse stdin (Claude Code hook input)
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            allow()
        hook_input: dict[str, Any] = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        log_event("ERROR", "Failed to parse hook input JSON")
        allow()  # Fail open — don't block legitimate use
        return  # Unreachable; satisfy type checker

    tool_name: str = hook_input.get("tool_name", "")

    # 2. Only act on Bash tool calls
    if tool_name != "Bash":
        allow()
        return

    command: str = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        allow()
        return

    cwd: str = hook_input.get("cwd", os.getcwd())
    session_id: str = hook_input.get("session_id", "unknown")

    # 3. Load rules & patterns
    rules = load_rules()
    patterns = get_patterns(rules)
    allowed_commands = get_allowed_commands(rules)
    require_confirmation = get_require_confirmation(rules)

    # 4. Check command against destructive patterns
    matched = check_command(command, patterns, allowed_commands)

    if not matched:
        allow()

    # 5. Build reason message
    rule_names = ", ".join(m["name"] for m in matched)
    descriptions = "; ".join(
        f"{m['name']}: {m['description']}" for m in matched
    )
    reason = (
        f"⚠️  DESTRUCTIVE COMMAND BLOCKED\n"
        f"   Command: {command[:200]}\n"
        f"   Matched rules: {rule_names}\n"
        f"   Details: {descriptions}\n"
        f"   Project: {cwd}\n"
        f"   If this is intentional, add the command to 'allowed_commands' in "
        f".claude/hooks/rules.json or run it manually in your terminal."
    )

    # 6. Log the blocked attempt
    log_event(
        "BLOCKED",
        "Destructive command intercepted",
        extra={
            "session_id": session_id,
            "command": command,
            "cwd": cwd,
            "matched_rules": [m["name"] for m in matched],
            "decision": "ask" if require_confirmation else "deny",
        },
    )

    # 7. Decide: deny or ask
    if require_confirmation:
        ask_user(reason)
    else:
        deny(reason)


if __name__ == "__main__":
    main()
