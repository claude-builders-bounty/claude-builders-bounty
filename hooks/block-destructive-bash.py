#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Block Destructive Bash Commands.

Intercepts dangerous Bash tool invocations before execution, logs every blocked
attempt to ~/.claude/hooks/blocked.log (timestamp, project path, attempted command),
and returns a clear message explaining to Claude why the command was blocked.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


# Each rule is (rule_id, regex_or_callable, human_explanation)
def _has_destructive_rm(command: str) -> Optional[str]:
    """Detect rm with both recursive (-r/-R/--recursive) and force (-f/--force) flags."""
    # Match combined flags like -rf, -fr, -Rf, -fR, -rfi, etc.
    if re.search(r"(?:^|[;&|()\s])(?:sudo\s+)?rm\s+[^;&|]*?(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", command, re.IGNORECASE):
        return "Recursive forced deletion (`rm -rf` / `rm -fr`) is blocked to prevent irreversible file loss."
    # Match separate flags like rm -r -f, rm --recursive --force, rm -f -r
    for segment in re.split(r"[;&|]+", command):
        if re.search(r"(?:^|\s)(?:sudo\s+)?rm(?:\s+|$)", segment):
            has_r = bool(re.search(r"(?:\s-[a-zA-Z]*[rR]|\s--recursive\b)", segment))
            has_f = bool(re.search(r"(?:\s-[a-zA-Z]*f|\s--force\b)", segment))
            if has_r and has_f:
                return "Recursive forced deletion (`rm --recursive --force` / `rm -r -f`) is blocked to prevent irreversible file loss."
    return None


def _has_drop_table(command: str) -> Optional[str]:
    """Detect SQL DROP TABLE / DROP DATABASE / DROP SCHEMA statements."""
    if re.search(r"\bDROP\s+(?:TABLE|DATABASE|SCHEMA)\b", command, re.IGNORECASE):
        return "Destructive SQL `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` statements are blocked."
    return None


def _has_truncate(command: str) -> Optional[str]:
    """Detect SQL TRUNCATE TABLE or standalone SQL TRUNCATE statements."""
    # Avoid matching the CLI binary `truncate -s 0 file` when used with flags, but catch SQL TRUNCATE [TABLE] <ident>
    if re.search(r"\bTRUNCATE\s+TABLE\b", command, re.IGNORECASE):
        return "Destructive SQL `TRUNCATE TABLE` statements are blocked."
    if re.search(r"(?:^|[;\"'`\s])TRUNCATE\s+(?!-[a-zA-Z])[a-zA-Z_][a-zA-Z0-9_.]*(?:\s*;|\s*$|\s+CASCADE|\s+RESTRICT|\s+CONTINUE|\s+RESTART)", command, re.IGNORECASE):
        return "Destructive SQL `TRUNCATE` statements are blocked."
    return None


def _has_unqualified_delete_from(command: str) -> Optional[str]:
    """Detect SQL DELETE FROM <table> without a WHERE clause."""
    # Inspect across SQL/command segments separated by semicolons, quotes, or newlines
    pattern = re.compile(
        r"\bDELETE\s+FROM\s+([a-zA-Z0-9_.`\"'\[\]]+)(.*?)(?:;|\"|'|`|\n|$)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(command):
        tail = match.group(2) or ""
        if not re.search(r"\bWHERE\b", tail, re.IGNORECASE):
            table = match.group(1)
            return f"Unqualified SQL `DELETE FROM {table}` without a `WHERE` clause is blocked to prevent wiping the entire table."
    return None


def _has_git_force_push(command: str) -> Optional[str]:
    """Detect git push --force or git push -f."""
    for segment in re.split(r"[;&|]+", command):
        if re.search(r"(?:^|\s)git\s+(?:-[^\s]+\s+)*push\b", segment):
            # Block --force (but not --force-with-lease unless --force is also passed) and -f
            tokens = segment.strip().split()
            for tok in tokens:
                if tok in ("--force", "-f") or tok.startswith("--force="):
                    return "Force-pushing (`git push --force` / `git push -f`) is blocked to protect remote commit history."
    return None


def _has_other_catastrophic_patterns(command: str) -> Optional[str]:
    """Detect fork bombs, raw disk formatting (mkfs), or dd writing to block devices."""
    if re.search(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", command):
        return "Fork bomb pattern (`:(){ :|:& };:`) is blocked."
    if re.search(r"(?:^|[;&|()\s])(?:sudo\s+)?mkfs(?:\.[a-zA-Z0-9]+)?\b", command):
        return "Filesystem formatting (`mkfs`) is blocked."
    if re.search(r"\bdd\b[^;&|]*\bof=/dev/(?:sd[a-z]|nvme\d+n\d+|vd[a-z]|hd[a-z]|disk\d+)\b", command):
        return "Raw block device overwrite (`dd of=/dev/...`) is blocked."
    return None


CHECKS = [
    ("rm -rf", _has_destructive_rm),
    ("DROP TABLE", _has_drop_table),
    ("git push --force", _has_git_force_push),
    ("TRUNCATE", _has_truncate),
    ("DELETE FROM without WHERE", _has_unqualified_delete_from),
    ("catastrophic system command", _has_other_catastrophic_patterns),
]


def evaluate_command(command: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluate a bash command string.
    Returns (is_blocked, matched_rule_name, reason).
    """
    if not command or not command.strip():
        return False, None, None

    for rule_name, checker in CHECKS:
        reason = checker(command)
        if reason:
            return True, rule_name, reason

    return False, None, None


def get_log_path() -> Path:
    custom = os.environ.get("CLAUDE_HOOK_LOG_FILE")
    if custom:
        return Path(custom).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_blocked_attempt(command: str, project_path: str, rule_name: str) -> None:
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sanitized_cmd = command.replace("\r", "\\r").replace("\n", "\\n")
    entry = f"[{timestamp}] | project={project_path} | rule={rule_name} | command={sanitized_cmd}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)


def parse_hook_input() -> Tuple[Optional[str], Optional[str], str]:
    """
    Parse Claude Code PreToolUse payload from stdin or environment variables.
    Returns (tool_name, command, project_path).
    """
    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    raw_stdin = ""
    if not sys.stdin.isatty():
        try:
            raw_stdin = sys.stdin.read()
        except Exception:
            raw_stdin = ""

    if raw_stdin.strip():
        try:
            payload = json.loads(raw_stdin)
            if isinstance(payload, dict):
                tool_name = payload.get("tool_name") or payload.get("tool") or "Bash"
                project_path = payload.get("cwd") or payload.get("project_dir") or project_path
                tool_input = payload.get("tool_input") or payload.get("input") or {}
                if isinstance(tool_input, dict):
                    command = tool_input.get("command") or tool_input.get("cmd") or ""
                elif isinstance(tool_input, str):
                    command = tool_input
                else:
                    command = ""
                return str(tool_name), str(command), str(project_path)
        except json.JSONDecodeError:
            # Treat raw stdin as command fallback if not JSON
            return "Bash", raw_stdin.strip(), project_path

    # Fallback: CLI arguments or environment variable
    if len(sys.argv) > 1:
        return "Bash", " ".join(sys.argv[1:]), project_path
    env_input = os.environ.get("CLAUDE_TOOL_INPUT")
    if env_input:
        try:
            data = json.loads(env_input)
            if isinstance(data, dict):
                return "Bash", str(data.get("command", "")), project_path
        except json.JSONDecodeError:
            return "Bash", env_input, project_path

    return None, None, project_path


def main() -> int:
    tool_name, command, project_path = parse_hook_input()
    if tool_name and tool_name.lower() not in ("bash", "shell", "execute_command", "run_command"):
        return 0
    if not command:
        return 0

    blocked, rule_name, reason = evaluate_command(command)
    if not blocked:
        return 0

    log_blocked_attempt(command, project_path, rule_name or "destructive_command")

    message = (
        f"[BLOCKED BY CLAUDE CODE HOOK] Destructive command intercepted ({rule_name}): {reason}\n"
        f"Attempted command: {command}\n"
        f"Project path: {project_path}\n"
        f"Logged to: {get_log_path()}\n"
        f"Please use a safer, non-destructive alternative or ask the user to run this command manually."
    )

    # Emit human-readable explanation to stderr (read by Claude Code when exit code is 2)
    sys.stderr.write(message + "\n")
    # Exit code 2 tells Claude Code PreToolUse hook to block execution and show stderr to Claude
    return 2


if __name__ == "__main__":
    sys.exit(main())
