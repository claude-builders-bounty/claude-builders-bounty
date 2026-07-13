#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Safety Hook
=====================================

A configurable pre-tool-use hook that intercepts dangerous bash commands
before they are executed by Claude Code. Blocks destructive patterns like
`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and
`DELETE FROM` (without a WHERE clause).

Usage:
    Reads JSON tool-call context from stdin (Claude Code hook protocol).
    Outputs a JSON deny decision to stdout when a dangerous command is detected.
    Exits 0 silently for safe commands (no decision → normal permission flow).

Configuration:
    Place hook_config.json alongside this script or at ~/.claude/hooks/hook_config.json
    to customise rules, whitelists, and logging behaviour.

Exit codes:
    0 — command is safe or hook has no opinion (normal flow continues)
    2 — command was blocked (Claude Code reads the deny decision from stdout)

License: MIT
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
__version__ = "1.2.0"

# ---------------------------------------------------------------------------
# ANSI colour helpers (disabled when NO_COLOR or TERM=dumb)
# ---------------------------------------------------------------------------
_NO_COLOUR = os.environ.get("NO_COLOR") is not None or os.environ.get("TERM") == "dumb"


def _c(code: str, text: str) -> str:
    if _NO_COLOUR:
        return text
    return f"\033[{code}m{text}\033[0m"


def red(t: str) -> str:
    return _c("1;31", t)


def yellow(t: str) -> str:
    return _c("1;33", t)


def dim(t: str) -> str:
    return _c("2", t)


# ---------------------------------------------------------------------------
# Default rules (used when no config file is found)
# ---------------------------------------------------------------------------
DEFAULT_RULES: list[dict[str, Any]] = [
    {
        "id": "rm-rf",
        "description": "Recursive force delete",
        "pattern": r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*\b|\-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*\b|(?:-[a-zA-Z]+\s+)*-r\s+(?:-[a-zA-Z]*\s+)*-f\b|(?:-[a-zA-Z]+\s+)*-f\s+(?:-[a-zA-Z]*\s+)*-r\b)",
        "severity": "critical",
        "enabled": True,
    },
    {
        "id": "drop-table",
        "description": "SQL DROP TABLE",
        "pattern": r"\bDROP\s+TABLE\b",
        "severity": "critical",
        "enabled": True,
        "flags": "IGNORECASE",
    },
    {
        "id": "git-push-force",
        "description": "Forced git push",
        "pattern": r"\bgit\s+push\s+.*--force\b|\bgit\s+push\s+-f\b",
        "severity": "high",
        "enabled": True,
    },
    {
        "id": "truncate",
        "description": "SQL TRUNCATE",
        "pattern": r"\bTRUNCATE\b",
        "severity": "critical",
        "enabled": True,
        "flags": "IGNORECASE",
    },
    {
        "id": "delete-no-where",
        "description": "SQL DELETE FROM without WHERE clause",
        "pattern": r"\bDELETE\s+FROM\s+\S+\s*;",
        "severity": "critical",
        "enabled": True,
        "flags": "IGNORECASE",
    },
    {
        "id": "delete-no-where-eol",
        "description": "SQL DELETE FROM without WHERE (end-of-line)",
        "pattern": r"\bDELETE\s+FROM\s+\S+\s*$",
        "severity": "critical",
        "enabled": True,
        "flags": "IGNORECASE|MULTILINE",
    },
    {
        "id": "chmod-777",
        "description": "World-writable permissions",
        "pattern": r"\bchmod\s+777\b",
        "severity": "high",
        "enabled": True,
    },
    {
        "id": "mkfs",
        "description": "Format filesystem",
        "pattern": r"\bmkfs\b",
        "severity": "critical",
        "enabled": True,
    },
    {
        "id": "dd-of-dev",
        "description": "Raw disk write with dd",
        "pattern": r"\bdd\b.*\bof=/dev/",
        "severity": "critical",
        "enabled": True,
    },
]

DEFAULT_CONFIG: dict[str, Any] = {
    "rules": DEFAULT_RULES,
    "whitelist": {
        "paths": [],
        "commands": [],
    },
    "logging": {
        "enabled": True,
        "log_file": "~/.claude/hooks/blocked.log",
        "max_size_mb": 10,
    },
    "dry_run": False,
    "show_colors": True,
}


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def _find_config() -> Path | None:
    """Search for hook_config.json in standard locations."""
    candidates = [
        Path(__file__).parent / "hook_config.json",
        Path.home() / ".claude" / "hooks" / "hook_config.json",
    ]
    env_path = os.environ.get("HOOK_CONFIG_PATH")
    if env_path:
        candidates.insert(0, Path(env_path))

    for p in candidates:
        if p.is_file():
            return p
    return None


def load_config() -> dict[str, Any]:
    """Load and merge config with defaults."""
    config = json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    cfg_path = _find_config()
    if cfg_path:
        try:
            with open(cfg_path) as f:
                user_cfg = json.load(f)
            # Merge top-level keys; rules replace entirely if provided
            if "rules" in user_cfg:
                config["rules"] = user_cfg["rules"]
            if "whitelist" in user_cfg:
                config["whitelist"].update(user_cfg["whitelist"])
            if "logging" in user_cfg:
                config["logging"].update(user_cfg["logging"])
            if "dry_run" in user_cfg:
                config["dry_run"] = user_cfg["dry_run"]
            if "show_colors" in user_cfg:
                config["show_colors"] = user_cfg["show_colors"]
        except (json.JSONDecodeError, OSError) as exc:
            print(f"Warning: could not load config {cfg_path}: {exc}", file=sys.stderr)
    return config


# ---------------------------------------------------------------------------
# Regex flag parser
# ---------------------------------------------------------------------------

_FLAG_MAP = {
    "IGNORECASE": re.IGNORECASE,
    "MULTILINE": re.MULTILINE,
    "DOTALL": re.DOTALL,
}


def _parse_flags(flag_str: str | None) -> int:
    if not flag_str:
        return 0
    flags = 0
    for part in flag_str.split("|"):
        flags |= _FLAG_MAP.get(part.strip(), 0)
    return flags


# ---------------------------------------------------------------------------
# Whitelist check
# ---------------------------------------------------------------------------

def _is_whitelisted(command: str, project_path: str, config: dict) -> bool:
    wl = config.get("whitelist", {})

    # Path whitelist
    for wp in wl.get("paths", []):
        wp_expanded = os.path.expanduser(wp)
        if project_path.startswith(wp_expanded):
            return True

    # Command whitelist (exact prefix match)
    for wc in wl.get("commands", []):
        if command.strip().startswith(wc):
            return True

    return False


# ---------------------------------------------------------------------------
# Rule matching
# ---------------------------------------------------------------------------

def check_command(command: str, rules: list[dict]) -> dict | None:
    """Return the first matching rule dict, or None."""
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        pattern = rule.get("pattern", "")
        flags = _parse_flags(rule.get("flags"))
        try:
            if re.search(pattern, command, flags):
                return rule
        except re.error:
            continue
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_blocked(
    command: str,
    rule: dict,
    project_path: str,
    config: dict,
    dry_run: bool = False,
) -> None:
    """Append a structured log line to the blocked log file."""
    log_cfg = config.get("logging", {})
    if not log_cfg.get("enabled", True):
        return

    log_path = Path(os.path.expanduser(log_cfg.get("log_file", "~/.claude/hooks/blocked.log")))
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Rotate if over max size
    max_bytes = log_cfg.get("max_size_mb", 10) * 1024 * 1024
    if log_path.exists() and log_path.stat().st_size > max_bytes:
        rotated = log_path.with_suffix(".log.1")
        if rotated.exists():
            rotated.unlink()
        log_path.rename(rotated)

    timestamp = datetime.now(timezone.utc).isoformat()
    entry = {
        "timestamp": timestamp,
        "command": command,
        "rule_id": rule.get("id", "unknown"),
        "rule_description": rule.get("description", ""),
        "severity": rule.get("severity", "unknown"),
        "project_path": project_path,
        "dry_run": dry_run,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Terminal output
# ---------------------------------------------------------------------------

def print_block_message(command: str, rule: dict, dry_run: bool = False) -> None:
    """Print a coloured warning to stderr."""
    mode = "[DRY-RUN] " if dry_run else ""
    severity = rule.get("severity", "unknown").upper()
    desc = rule.get("description", rule.get("id", "unknown"))

    print("", file=sys.stderr)
    print(red(f"  ╔══════════════════════════════════════════════════════════╗"), file=sys.stderr)
    print(red(f"  ║  🛑  {mode}DANGEROUS COMMAND BLOCKED                       ║"), file=sys.stderr)
    print(red(f"  ╠══════════════════════════════════════════════════════════╣"), file=sys.stderr)
    print(red(f"  ║  Rule:     ") + yellow(f"{desc:<45}") + red("║"), file=sys.stderr)
    print(red(f"  ║  Severity: ") + yellow(f"{severity:<45}") + red("║"), file=sys.stderr)
    print(red(f"  ║  Command:  ") + dim(f"{command[:45]:<45}") + red("║"), file=sys.stderr)
    print(red(f"  ╚══════════════════════════════════════════════════════════╝"), file=sys.stderr)
    print("", file=sys.stderr)


# ---------------------------------------------------------------------------
# Main hook logic
# ---------------------------------------------------------------------------

def make_deny_response(reason: str) -> dict:
    """Build the Claude Code deny JSON response."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def process_hook(input_data: dict, config: dict | None = None) -> int:
    """
    Process a single hook invocation.

    Returns exit code: 0 = safe, 2 = blocked.
    """
    if config is None:
        config = load_config()

    # Extract the command from Claude Code's tool input
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # We only care about Bash tool calls
    if tool_name not in ("Bash", "bash", "shell", "terminal"):
        return 0

    command = tool_input.get("command", "")
    if not command:
        return 0

    project_path = input_data.get("project_path", os.getcwd())

    # Whitelist check
    if _is_whitelisted(command, project_path, config):
        return 0

    # Check rules
    matched_rule = check_command(command, config.get("rules", []))
    if matched_rule is None:
        return 0

    dry_run = config.get("dry_run", False)

    # Log
    log_blocked(command, matched_rule, project_path, config, dry_run=dry_run)

    # Terminal warning
    print_block_message(command, matched_rule, dry_run=dry_run)

    if dry_run:
        # In dry-run mode, let the command through
        return 0

    # Build deny response
    reason = (
        f"🛑 Blocked by safety hook: {matched_rule.get('description', matched_rule.get('id'))} "
        f"[severity={matched_rule.get('severity', 'unknown')}]. "
        f"Command: {command!r}"
    )
    response = make_deny_response(reason)
    print(json.dumps(response))
    return 2


def main() -> None:
    """Entry point: read stdin, process, exit."""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        input_data = json.loads(raw)
    except (json.JSONDecodeError, OSError):
        # If we can't parse input, don't block anything
        sys.exit(0)

    config = load_config()
    exit_code = process_hook(input_data, config)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
