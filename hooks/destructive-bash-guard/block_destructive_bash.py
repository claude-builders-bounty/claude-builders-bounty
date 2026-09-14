#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook: Block Destructive Bash Commands

Intercepts tool execution requests in Claude Code and prevents destructive shell operations:
- rm -rf (and recursive force variants)
- DROP TABLE (SQL)
- git push --force (and force-with-lease variants)
- TRUNCATE (SQL)
- DELETE FROM without a WHERE clause

Official Claude Code PreToolUse Blocking Protocol:
On blocked command:
  stdout: JSON with hookSpecificOutput.permissionDecision = "deny"
  exit: 0
On allowed command:
  exit: 0 (no deny decision)

Installation:
  python3 ~/.claude/hooks/pre-tool-use.py --install
  Safely and idempotently registers the hook in ~/.claude/settings.json.

Logs blocked attempts to ~/.claude/hooks/blocked.log with:
- Timestamp (UTC ISO-8601)
- Attempted command
- Project path
- Reason
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _split_subcommands(cmd_line: str) -> List[str]:
    """Split compound command lines into subcommands while respecting pipelines."""
    parts = re.split(r"(?:&&|\|\||;|\|\|\n)", cmd_line)
    return [p.strip() for p in parts if p.strip()]


def _is_echo_or_print_command(subcmd: str) -> bool:
    """Check if subcommand is pure text display (echo, printf) without execution."""
    tokens = subcmd.strip().split()
    if not tokens:
        return False
    return tokens[0].lower() in ("echo", "printf")


def is_destructive_command(cmd_str: str) -> Tuple[bool, Optional[str]]:
    """
    Analyze a shell command string for prohibited destructive patterns.
    Returns: (is_destructive: bool, reason: Optional[str])
    """
    if not cmd_str or not cmd_str.strip():
        return False, None

    normalized = cmd_str.strip()
    subcommands = _split_subcommands(normalized)

    for subcmd in subcommands:
        if _is_echo_or_print_command(subcmd):
            continue

        sub_tokens = subcmd.split()
        if not sub_tokens:
            continue

        exe = sub_tokens[0].lower()

        # 1. rm -rf variants
        if exe == "rm" or exe.endswith("/rm") or exe.endswith("\\rm"):
            flags = [t for t in sub_tokens[1:] if t.startswith("-") and not t.startswith("--")]
            long_flags = [t for t in sub_tokens[1:] if t.startswith("--")]
            has_r = any("r" in f or "R" in f for f in flags) or "--recursive" in long_flags
            has_f = any("f" in f or "F" in f for f in flags) or "--force" in long_flags
            if has_r and has_f:
                return True, "Recursive force removal ('rm -rf') is prohibited to prevent accidental directory deletion."

        # 2. git push --force variants
        if exe == "git" or exe.endswith("/git") or exe.endswith("\\git"):
            if len(sub_tokens) >= 2 and sub_tokens[1].lower() == "push":
                force_flags = {"--force", "-f", "--force-with-lease", "--force-if-includes"}
                if any(t in force_flags or t.startswith("--force") for t in sub_tokens[2:]):
                    return True, "'git push --force' is prohibited to prevent remote git history overwrites."

        # 3. SQL DROP TABLE
        if re.search(r"\bDROP\s+TABLE\b", subcmd, re.IGNORECASE):
            return True, "SQL 'DROP TABLE' statement is prohibited to prevent schema destruction."

        # 4. SQL TRUNCATE
        if re.search(r"\bTRUNCATE\s+(?:TABLE\s+)?[a-zA-Z0-9_`\"\[\]\.]+", subcmd, re.IGNORECASE):
            return True, "SQL 'TRUNCATE' statement is prohibited to prevent bulk data deletion."

        # 5. SQL DELETE FROM without WHERE
        delete_from_match = re.search(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_`\"\[\]\.]+)([\s\S]*)", subcmd, re.IGNORECASE)
        if delete_from_match:
            remainder = delete_from_match.group(2)
            sql_stmts = remainder.split(";")
            target_stmt_tail = sql_stmts[0]
            if not re.search(r"\bWHERE\b", target_stmt_tail, re.IGNORECASE):
                return True, "SQL 'DELETE FROM' without a WHERE clause is prohibited to prevent accidental table-wide deletion."

    return False, None


def log_blocked_attempt(
    command: str,
    project_path: str,
    reason: str,
    log_file_override: Optional[str] = None,
) -> None:
    """Log blocked attempt to ~/.claude/hooks/blocked.log (or override for testing)."""
    now_iso = datetime.now(timezone.utc).isoformat()
    if log_file_override:
        log_path = Path(log_file_override)
    else:
        log_path = Path.home() / ".claude" / "hooks" / "blocked.log"

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_entry = (
            f"[{now_iso}] BLOCKED\n"
            f"  Command:      {command}\n"
            f"  Project Path: {project_path}\n"
            f"  Reason:       {reason}\n"
            f"----------------------------------------------------------------------\n"
        )
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        sys.stderr.write(f"[WARNING] Could not write to blocked.log: {e}\n")


def install_hook(claude_dir_override: Optional[str] = None) -> int:
    """
    Safely registers the pre-tool-use hook in ~/.claude/settings.json (or override).
    - Idempotent
    - Preserves existing settings and other hooks
    - Fails closed on malformed JSON without overwriting
    """
    if claude_dir_override:
        claude_dir = Path(claude_dir_override)
    elif os.environ.get("CLAUDE_HOME_OVERRIDE"):
        claude_dir = Path(os.environ["CLAUDE_HOME_OVERRIDE"]) / ".claude"
    else:
        claude_dir = Path.home() / ".claude"

    hooks_dir = claude_dir / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    settings_file = claude_dir / "settings.json"
    settings: Dict[str, Any] = {}

    if settings_file.exists():
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    settings = json.loads(content)
                    if not isinstance(settings, dict):
                        sys.stderr.write("[ERROR] settings.json is not a valid JSON object. Aborting to prevent data loss.\n")
                        return 1
        except Exception as e:
            sys.stderr.write(f"[ERROR] Failed to parse existing {settings_file}: {e}. Aborting to prevent overwriting.\n")
            return 1

    if "hooks" not in settings or not isinstance(settings["hooks"], dict):
        settings["hooks"] = {}

    if "PreToolUse" not in settings["hooks"] or not isinstance(settings["hooks"]["PreToolUse"], list):
        settings["hooks"]["PreToolUse"] = []

    target_hook_entry = {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/pre-tool-use.py"
    }

    already_registered = False
    for entry in settings["hooks"]["PreToolUse"]:
        if isinstance(entry, dict):
            matcher = entry.get("matcher")
            cmd = entry.get("command", "")
            if matcher == "Bash" and "pre-tool-use.py" in cmd:
                already_registered = True
                break

    if not already_registered:
        settings["hooks"]["PreToolUse"].append(target_hook_entry)

    try:
        with open(settings_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
        print(f"[SUCCESS] Destructive bash guard hook successfully registered in {settings_file}")
        return 0
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to write {settings_file}: {e}\n")
        return 1


def main() -> int:
    """
    Entry point for Claude Code PreToolUse hook.
    Supports --install mode and standard PreToolUse JSON protocol.
    """
    if "--install" in sys.argv:
        return install_hook()

    command = ""
    project_path = os.getcwd()

    # Case A: Input passed as JSON payload on stdin (standard Claude Code PreToolUse hook protocol)
    if not sys.stdin.isatty():
        try:
            stdin_content = sys.stdin.read().strip()
            if stdin_content:
                data = json.loads(stdin_content)
                # Parse tool_name and command from standard Claude Code hook schema
                tool_name = str(data.get("tool_name") or data.get("toolName") or data.get("tool") or "").lower()
                tool_input = data.get("tool_input") or data.get("toolInput") or data.get("input") or {}
                if isinstance(tool_input, dict):
                    command = str(tool_input.get("command") or tool_input.get("cmd") or "")
                elif isinstance(tool_input, str):
                    command = tool_input

                project_path = str(data.get("cwd") or data.get("project_path") or data.get("projectPath") or os.getcwd())

                # If hook is invoked for a non-Bash tool, allow immediately
                if tool_name and tool_name not in ("bash", "execute_command", "terminal"):
                    return 0
        except Exception:
            # Fallback if stdin is plain text command
            command = stdin_content

    # Case B: Command passed via CLI arguments (for testing or direct runner)
    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        # Nothing to check, allow
        return 0

    is_blocked, reason = is_destructive_command(command)

    if is_blocked:
        block_reason = reason or "Prohibited destructive command."
        log_override = os.environ.get("CLAUDE_HOOK_LOG_OVERRIDE")
        log_blocked_attempt(command, project_path, block_reason, log_file_override=log_override)

        # Official Claude Code PreToolUse structured denial response on stdout with exit code 0
        response = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"Destructive command blocked by security hook: {block_reason} (Command: {command})"
            }
        }
        sys.stdout.write(json.dumps(response, indent=2) + "\n")
        return 0

    # Allowed command: exit 0 with no denial output
    return 0


if __name__ == "__main__":
    sys.exit(main())
