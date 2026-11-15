#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Bash Command Guard (Issue #3)
Intercepts dangerous bash commands before Claude Code executes them:
- rm -rf
- DROP TABLE
- git push --force (or -f)
- TRUNCATE
- DELETE FROM without a WHERE clause

Follows the official Claude Code hooks specification (`~/.claude/hooks/`):
- Reads tool invocation JSON from stdin (or CLI `--command` for testing/self-verification).
- Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.
- Outputs a structured JSON block decision AND clear stderr explanation (exit code 2 on block, 0 on allow).
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any

DESTRUCTIVE_RULES: List[Tuple[str, re.Pattern, str]] = [
    (
        "RM_RF",
        re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|--recursive\s+--force|--force\s+--recursive|-[a-zA-Z]*f[a-zA-Z]*r)\b", re.IGNORECASE),
        "Recursive forced deletion (`rm -rf`) is blocked to prevent irreversible filesystem data loss."
    ),
    (
        "DROP_TABLE",
        re.compile(r"\bDROP\s+TABLE\b", re.IGNORECASE),
        "SQL `DROP TABLE` statement is blocked to prevent destructive schema removal."
    ),
    (
        "GIT_PUSH_FORCE",
        re.compile(r"\bgit\s+push\b[^\n;|&]*(\s--force\b|\s--force-with-lease\b|\s-f\b)", re.IGNORECASE),
        "Force-pushing (`git push --force` / `-f`) is blocked to protect remote commit history."
    ),
    (
        "TRUNCATE_TABLE",
        re.compile(r"\bTRUNCATE\s+(TABLE\s+)?[a-zA-Z0-9_`\"'.]+", re.IGNORECASE),
        "SQL `TRUNCATE` operation is blocked to prevent unrecoverable table data wiping."
    ),
]

DELETE_FROM_RE = re.compile(r"\bDELETE\s+FROM\s+[a-zA-Z0-9_`\"'.]+(?P<tail>[^;]*)", re.IGNORECASE)
WHERE_CLAUSE_RE = re.compile(r"\bWHERE\b", re.IGNORECASE)


def evaluate_command(command: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Evaluates a bash command string against destructive command patterns.
    Returns (is_blocked, rule_id, explanation).
    """
    if not command or not command.strip():
        return False, None, None

    for rule_id, pattern, reason in DESTRUCTIVE_RULES:
        if pattern.search(command):
            return True, rule_id, reason

    # Check DELETE FROM without a WHERE clause
    for match in DELETE_FROM_RE.finditer(command):
        tail = match.group("tail") or ""
        if not WHERE_CLAUSE_RE.search(tail):
            return (
                True,
                "DELETE_WITHOUT_WHERE",
                "SQL `DELETE FROM` without a `WHERE` clause is blocked to prevent full-table deletion."
            )

    return False, None, None


def log_blocked_attempt(command: str, project_path: str, rule_id: str, log_file: Optional[Path] = None) -> Path:
    """
    Appends a structured audit entry to `~/.claude/hooks/blocked.log`
    with timestamp, attempted command, and project path.
    """
    target_log = log_file or (Path.home() / ".claude" / "hooks" / "blocked.log")
    target_log.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat()
    clean_cmd = re.sub(r"[\r\n]+", " ", command).strip()
    entry = f"[{ts}] RULE={rule_id} | PROJECT={project_path} | COMMAND={clean_cmd}\n"
    with open(target_log, "a", encoding="utf-8") as f:
        f.write(entry)
    return target_log


def extract_command_and_cwd(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Extracts bash command and project path from Claude Code PreToolUse stdin JSON."""
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "Bash")
    if tool_name.lower() not in {"bash", "shell", "execute_command", "run_command"}:
        return "", str(payload.get("cwd") or os.getcwd())

    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if isinstance(tool_input, dict):
        cmd = str(tool_input.get("command") or tool_input.get("cmd") or "")
    elif isinstance(tool_input, str):
        cmd = tool_input
    else:
        cmd = ""

    cwd = str(payload.get("cwd") or payload.get("project_dir") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    return cmd, cwd


def run_self_test() -> int:
    """Runs built-in verification test cases when invoked with --self-test."""
    test_cases = [
        ("rm -rf /tmp/build_artifacts", True, "RM_RF"),
        ("psql -c 'DROP TABLE users;'", True, "DROP_TABLE"),
        ("git push --force origin main", True, "GIT_PUSH_FORCE"),
        ("sqlite3 app.db 'TRUNCATE TABLE sessions;'", True, "TRUNCATE_TABLE"),
        ("psql -c 'DELETE FROM orders;'", True, "DELETE_WITHOUT_WHERE"),
        ("psql -c 'DELETE FROM orders WHERE id = 42;'", False, None),
        ("ls -la && git status && pytest", False, None),
        ("git push origin feat/safe-branch", False, None),
    ]
    for cmd, expected_blocked, expected_rule in test_cases:
        blocked, rule, _ = evaluate_command(cmd)
        if blocked != expected_blocked or rule != expected_rule:
            print(f"[FAIL] Command: {cmd} -> got ({blocked}, {rule}), expected ({expected_blocked}, {expected_rule})", file=sys.stderr)
            return 1
    print(json.dumps({
        "status": "VERIFIED_READY",
        "hook": "pre_tool_use_guard.py",
        "tests_passed": len(test_cases)
    }))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Claude Code PreToolUse Destructive Bash Guard")
    parser.add_argument("fixture", nargs="?", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--command", help="Evaluate a single command string directly")
    parser.add_argument("--project-path", default=None, help="Override project path for logging")
    parser.add_argument("--log-file", default=None, help="Override blocked.log path")
    parser.add_argument("--self-test", action="store_true", help="Run built-in verification suite")
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()

    log_path = Path(args.log_file) if args.log_file else None
    project_path = args.project_path or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if args.command is not None:
        command = args.command
    elif not sys.stdin.isatty():
        raw_stdin = sys.stdin.read().strip()
        if not raw_stdin:
            return run_self_test()
        try:
            payload = json.loads(raw_stdin)
            command, project_path = extract_command_and_cwd(payload)
        except json.JSONDecodeError:
            command = raw_stdin
    else:
        return run_self_test()

    blocked, rule_id, reason = evaluate_command(command)
    if blocked and rule_id and reason:
        recorded_log = log_blocked_attempt(command, project_path, rule_id, log_file=log_path)
        explanation = (
            f"🛑 [Claude Code Hook Blocked — {rule_id}] {reason}\n"
            f"Attempted command: `{command}`\n"
            f"Project path: `{project_path}`\n"
            f"Logged to: `{recorded_log}`\n"
            f"Please use a targeted, non-destructive alternative or ask the user for explicit confirmation."
        )
        print(explanation, file=sys.stderr)
        print(json.dumps({
            "decision": "block",
            "reason": explanation
        }))
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
