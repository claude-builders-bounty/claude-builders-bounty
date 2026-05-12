#!/usr/bin/env python3
"""Claude Code PreToolUse guard for destructive Bash commands.

The hook reads Claude Code's hook JSON from stdin. Safe commands exit 0 with no
output. Blocked commands are logged and returned as a structured PreToolUse deny
response so Claude sees a clear reason before the Bash tool executes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

HOOK_EVENT = "PreToolUse"
DEFAULT_LOG = Path("~/.claude/hooks/blocked.log").expanduser()
DEFAULT_SETTINGS = Path("~/.claude/settings.json").expanduser()

SHELL_SEPARATORS = {";", "&&", "||", "|", "&"}
SAFE_TEXT_COMMANDS = {
    "cat",
    "echo",
    "printf",
    "grep",
    "egrep",
    "fgrep",
    "rg",
    "sed",
    "awk",
    "perl",
    "python",
    "python3",
    "node",
}
DB_CLIENTS = {
    "sqlite3",
    "psql",
    "mysql",
    "mariadb",
    "turso",
    "duckdb",
    "clickhouse-client",
}


@dataclass(frozen=True)
class Finding:
    blocked: bool
    reason: str = ""
    rule: str = ""


@dataclass(frozen=True)
class Decision:
    blocked: bool
    command: str = ""
    project_path: str = ""
    reason: str = ""
    rule: str = ""


def _shell_tokens(command: str) -> list[str]:
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        # If quoting is malformed, fall back to a conservative whitespace split.
        return command.split()


def _command_groups(tokens: Iterable[str]) -> Iterable[list[str]]:
    group: list[str] = []
    for token in tokens:
        if token in SHELL_SEPARATORS or set(token) <= {";", "&", "|"}:
            if group:
                yield group
                group = []
            continue
        if token in {"(", ")"}:
            continue
        group.append(token)
    if group:
        yield group


def _has_rm_recursive_force(group: list[str]) -> bool:
    if not group or Path(group[0]).name != "rm":
        return False
    recursive = False
    force = False
    for arg in group[1:]:
        if arg == "--":
            continue
        if arg in {"--recursive", "--dir"}:
            recursive = True
            continue
        if arg == "--force":
            force = True
            continue
        if arg.startswith("--"):
            continue
        if arg.startswith("-") and len(arg) > 1:
            flags = arg[1:]
            recursive = recursive or any(ch in flags for ch in "rR")
            force = force or "f" in flags
    return recursive and force


def _has_force_push(group: list[str]) -> bool:
    if len(group) < 2 or Path(group[0]).name != "git" or group[1] != "push":
        return False
    for arg in group[2:]:
        if arg in {"-f", "--force", "--force-with-lease"}:
            return True
        if arg.startswith("--force-with-lease="):
            return True
    return False


def _strip_sql_strings(sql: str) -> str:
    # Remove single/double-quoted SQL strings so `WHERE` inside a literal does not
    # accidentally make an unbounded DELETE look safe.
    return re.sub(r"'([^']|'')*'|\"([^\"]|\"\")*\"", "''", sql)


def _sql_finding(sql: str) -> Finding:
    normalized = _strip_sql_strings(sql)
    upper = re.sub(r"\s+", " ", normalized).upper()
    if re.search(r"\bDROP\s+TABLE\b", upper):
        return Finding(True, "Blocked DROP TABLE statement", "drop-table")
    if re.search(r"\bTRUNCATE\b", upper):
        return Finding(True, "Blocked TRUNCATE statement", "truncate")
    for statement in re.split(r";", upper):
        match = re.search(r"\bDELETE\s+FROM\b", statement)
        if match and not re.search(r"\bWHERE\b", statement[match.end() :]):
            return Finding(True, "Blocked DELETE FROM without a WHERE clause", "delete-without-where")
    return Finding(False)


def _maybe_sql_group(group: list[str]) -> str | None:
    if not group:
        return None
    executable = Path(group[0]).name
    if executable in SAFE_TEXT_COMMANDS:
        return None
    joined = " ".join(group)
    first = group[0].upper()
    if first in {"DROP", "TRUNCATE", "DELETE"}:
        return joined
    if executable in DB_CLIENTS:
        return joined
    # Shell wrappers often pass the SQL as a direct argument to a DB client.
    if any(Path(tok).name in DB_CLIENTS for tok in group[:3]):
        return joined
    return None


def inspect_command(command: str) -> Finding:
    """Return the first destructive-command finding for a Bash command string."""
    for group in _command_groups(_shell_tokens(command)):
        if _has_rm_recursive_force(group):
            return Finding(True, "Blocked recursive forced rm command", "rm-recursive-force")
        if _has_force_push(group):
            return Finding(True, "Blocked git force push", "git-force-push")
        sql = _maybe_sql_group(group)
        if sql:
            finding = _sql_finding(sql)
            if finding.blocked:
                return finding
    return Finding(False)


def extract_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") if isinstance(tool_input, dict) else None
    return command if isinstance(command, str) else ""


def project_path_from(payload: dict[str, Any]) -> str:
    for key in ("cwd", "project_dir", "workspace", "transcript_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value if key != "transcript_path" else str(Path(value).parent)
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("PWD") or os.getcwd()


def evaluate_payload(payload: dict[str, Any]) -> Decision:
    if payload.get("tool_name") != "Bash":
        return Decision(False, project_path=project_path_from(payload))
    command = extract_command(payload)
    finding = inspect_command(command)
    return Decision(
        blocked=finding.blocked,
        command=command,
        project_path=project_path_from(payload),
        reason=finding.reason,
        rule=finding.rule,
    )


def log_block(decision: Decision, log_path: Path | None = None) -> None:
    path = log_path or Path(os.environ.get("CLAUDE_HOOK_LOG", str(DEFAULT_LOG))).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project_path": decision.project_path,
        "attempted_command": decision.command,
        "rule": decision.rule,
        "reason": decision.reason,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def deny_output(decision: Decision) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": HOOK_EVENT,
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"{decision.reason}. The attempted Bash command was logged to "
                f"{Path(os.environ.get('CLAUDE_HOOK_LOG', str(DEFAULT_LOG))).expanduser()}. "
                "Use a narrower, reversible command or add an explicit WHERE/backup step."
            ),
        }
    }


def install_settings(settings_path: Path = DEFAULT_SETTINGS, hook_path: Path | None = None) -> None:
    hook = Path(hook_path or Path(__file__).resolve()).expanduser()
    settings_path = settings_path.expanduser()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any]
    if settings_path.exists() and settings_path.read_text().strip():
        data = json.loads(settings_path.read_text())
    else:
        data = {}
    hooks = data.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])
    command = f"python3 {shlex.quote(str(hook))}"
    entry = {"type": "command", "command": command}

    for group in pre:
        if group.get("matcher") == "Bash":
            existing = group.setdefault("hooks", [])
            if not any(h.get("command") == command for h in existing if isinstance(h, dict)):
                existing.append(entry)
            break
    else:
        pre.append({"matcher": "Bash", "hooks": [entry]})

    settings_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code destructive Bash PreToolUse guard")
    parser.add_argument("--install-settings", action="store_true", help="merge this hook into ~/.claude/settings.json")
    parser.add_argument("--settings", type=Path, default=DEFAULT_SETTINGS, help="settings path for --install-settings")
    args = parser.parse_args(argv)

    if args.install_settings:
        install_settings(settings_path=args.settings)
        print(f"Installed PreToolUse Bash guard in {args.settings.expanduser()}")
        return 0

    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            return 0
        decision = evaluate_payload(payload)
        if decision.blocked:
            log_block(decision)
            print(json.dumps(deny_output(decision), ensure_ascii=False))
        return 0
    except Exception as exc:  # fail open: hooks should not brick normal Claude usage
        print(f"destructive_guard hook failed open: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
