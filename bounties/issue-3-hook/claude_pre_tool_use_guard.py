#!/usr/bin/env python3
"""Claude Code PreToolUse hook that blocks destructive Bash commands.

The hook reads Claude Code hook JSON from stdin. For Bash tool calls, it
detects high-risk destructive shell/SQL patterns, logs blocked attempts to
~/.claude/hooks/blocked.log, and returns protocol-correct PreToolUse JSON with
permissionDecision="deny". Safe commands are allowed silently.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any, Iterable, NamedTuple

HOOK_NAME = "claude_pre_tool_use_guard"
LOG_PATH = Path.home() / ".claude" / "hooks" / "blocked.log"
HOOK_INSTALL_PATH = Path.home() / ".claude" / "hooks" / "claude_pre_tool_use_guard.py"
SETTINGS_PATH = Path.home() / ".claude" / "settings.json"

DB_CLIENTS = {
    "psql",
    "mysql",
    "mariadb",
    "sqlite3",
    "duckdb",
    "sqlcmd",
    "isql",
    "clickhouse-client",
}
SAFE_TEXT_COMMANDS = {
    "echo",
    "printf",
    "grep",
    "egrep",
    "fgrep",
    "rg",
    "ag",
    "ack",
    "sed",
    "awk",
    "cat",
    "less",
    "more",
    "bat",
    "python",
    "python3",
    "node",
    "perl",
    "ruby",
}
WRAPPER_COMMANDS = {
    "sudo",
    "doas",
    "command",
    "builtin",
    "time",
    "env",
    "noglob",
    "xargs",
}
SHELL_OPERATORS = {";", "&&", "||", "|"}


class BlockDecision(NamedTuple):
    rule: str
    reason: str


def _basename(token: str) -> str:
    return os.path.basename(token.strip())


def _tokenize(command: str) -> list[str]:
    """Tokenize shell-ish input while retaining shell operators when possible."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        # Unbalanced quotes should not create a bypass. Fall back to a rough split.
        return re.findall(r"&&|\|\||[;|]|\S+", command)


def _command_substitution_fragments(command: str) -> list[str]:
    """Extract simple shell command substitutions so nested destructive commands are blocked."""
    fragments = re.findall(r"\$\(([^()]*)\)", command, flags=re.S)
    fragments.extend(re.findall(r"`([^`]*)`", command, flags=re.S))
    return [fragment.strip() for fragment in fragments if fragment.strip()]


def _segments(tokens: Iterable[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in SHELL_OPERATORS:
            if current:
                segments.append(current)
                current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _skip_assignments_and_wrappers(tokens: list[str]) -> list[str]:
    i = 0
    while i < len(tokens):
        base = _basename(tokens[i])
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
            i += 1
            continue
        if base in WRAPPER_COMMANDS:
            i += 1
            if base == "env":
                # env may carry options and KEY=VALUE assignments before the command.
                while i < len(tokens) and (
                    tokens[i].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i])
                ):
                    i += 1
            elif base == "xargs":
                # Skip common xargs flags so `... | xargs rm -rf` is caught.
                while i < len(tokens) and tokens[i].startswith("-"):
                    i += 1
            continue
        break
    return tokens[i:]


def _first_executable(tokens: list[str]) -> str:
    stripped = _skip_assignments_and_wrappers(tokens)
    return _basename(stripped[0]) if stripped else ""


def _detect_rm_rf(segments: list[list[str]]) -> BlockDecision | None:
    for segment in segments:
        if _first_executable(segment) in SAFE_TEXT_COMMANDS:
            # Avoid blocking harmless docs/search commands that mention rm -rf.
            continue
        for start in range(len(segment)):
            tokens = _skip_assignments_and_wrappers(segment[start:])
            if not tokens or _basename(tokens[0]) != "rm":
                continue

            recursive = False
            force = False
            stop_options = False

            for token in tokens[1:]:
                if token == "--":
                    stop_options = True
                    continue
                if not stop_options and token.startswith("--"):
                    if token in {"--recursive", "--dir", "--recursive=true"}:
                        recursive = True
                    if token in {"--force", "--force=true"}:
                        force = True
                    continue
                if not stop_options and token.startswith("-") and token != "-":
                    flags = token.lstrip("-")
                    if "r" in flags or "R" in flags:
                        recursive = True
                    if "f" in flags:
                        force = True

            if recursive and force:
                return BlockDecision(
                    "rm-rf",
                    "Blocked recursive forced deletion (`rm -rf` / equivalent). This can irreversibly delete project or system files.",
                )
    return None


def _git_subcommand_tokens(tokens: list[str]) -> list[str] | None:
    tokens = _skip_assignments_and_wrappers(tokens)
    if not tokens or _basename(tokens[0]) != "git":
        return None
    i = 1
    options_with_values = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--exec-path"}
    while i < len(tokens):
        token = tokens[i]
        if token == "--":
            i += 1
            break
        if token in options_with_values:
            i += 2
            continue
        if any(token.startswith(prefix + "=") for prefix in options_with_values if prefix.startswith("--")):
            i += 1
            continue
        if token.startswith("-") and not token.startswith("--"):
            i += 1
            continue
        if token.startswith("--"):
            i += 1
            continue
        break
    return tokens[i:]


def _is_git_force_flag(token: str) -> bool:
    if token in {"--force", "--force-with-lease", "--force-if-includes"}:
        return True
    if token.startswith("--force=") or token.startswith("--force-with-lease="):
        return True
    return token.startswith("-") and not token.startswith("--") and "f" in token[1:]


def _detect_git_force_push(segments: list[list[str]]) -> BlockDecision | None:
    for segment in segments:
        tokens = _git_subcommand_tokens(segment)
        if not tokens or tokens[0] != "push":
            continue
        for token in tokens[1:]:
            if _is_git_force_flag(token):
                return BlockDecision(
                    "git-force-push",
                    "Blocked forced git push. Rewriting remote history can overwrite other contributors' work.",
                )
            if token.startswith("+") and len(token) > 1:
                return BlockDecision(
                    "git-force-push",
                    "Blocked forced git push refspec. Leading `+` rewrites remote history.",
                )
    return None


def _sql_search_text(segments: list[list[str]]) -> str:
    """Return shell-tokenized text with shell quotes removed but contents kept.

    Claude Code Bash tool input is a shell command, so SQL is commonly passed as
    a quoted argument to clients such as `psql -c "DROP TABLE users"`. Using
    shlex-tokenized text lets us inspect the SQL payload without mistaking the
    shell quotes themselves for SQL string delimiters.
    """
    return "\n".join(" ".join(segment) for segment in segments)


def _strip_postgres_dollar_quotes(sql: str) -> str:
    """Remove PostgreSQL dollar-quoted string bodies before SQL keyword checks."""
    pattern = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)\$.*?\$\1\$|\$\$.*?\$\$", re.S)
    previous = None
    while previous != sql:
        previous = sql
        sql = pattern.sub(" ", sql)
    return sql


def _strip_sql_literals_and_comments(sql: str) -> str:
    """Remove SQL string/comment text so fake WHERE/comment markers cannot bypass checks."""
    out: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(sql):
        ch = sql[i]

        if quote:
            if ch == quote:
                # SQL escapes quotes by doubling them, e.g. 'it''s'.
                if i + 1 < len(sql) and sql[i + 1] == quote:
                    i += 2
                    continue
                quote = None
            i += 1
            continue

        if sql.startswith("--", i):
            # Skip line comment text but preserve the newline boundary.
            newline = sql.find("\n", i + 2)
            if newline == -1:
                break
            out.append("\n")
            i = newline + 1
            continue
        if sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            i = len(sql) if end == -1 else end + 2
            out.append(" ")
            continue
        if ch in {"'", '"', "`"}:
            quote = ch
            i += 1
            continue

        out.append(ch)
        i += 1
    return "".join(out)


def _split_sql_statements(text: str) -> list[str]:
    return [part.strip() for part in text.split(";") if part.strip()]



def _contains_db_execution_context(command: str, segments: list[list[str]]) -> bool:
    for segment in segments:
        exe = _first_executable(segment)
        if exe in DB_CLIENTS:
            return True
        joined = " ".join(segment).lower()
        if "prisma db execute" in joined or "supabase db" in joined:
            return True
        if re.search(r"\b(rails|rake)\s+db", joined):
            return True
    lowered = command.lower()
    return bool(re.search(r"\|\s*(psql|mysql|mariadb|sqlite3|duckdb|sqlcmd)\b", lowered))


def _looks_like_safe_text_inspection(command: str, segments: list[list[str]]) -> bool:
    """Avoid blocking docs/search commands that merely mention dangerous SQL."""
    if _contains_db_execution_context(command, segments):
        return False
    first = _first_executable(segments[0]) if segments else ""
    if first not in SAFE_TEXT_COMMANDS:
        return False
    lowered = command.lower()
    # Redirection or a DB client in a pipeline can turn text into an executed script.
    if ">" in command or re.search(r"\|\s*(psql|mysql|mariadb|sqlite3|duckdb|sqlcmd)\b", lowered):
        return False
    return True


def _direct_sql_statement(command: str) -> bool:
    return bool(re.match(r"^\s*(drop\s+table|truncate\b|delete\s+from)\b", command, re.I))


def _detect_sql_destructive(command: str, segments: list[list[str]]) -> BlockDecision | None:
    sql = _strip_sql_literals_and_comments(_strip_postgres_dollar_quotes(_sql_search_text(segments)))
    db_context = _contains_db_execution_context(command, segments)
    direct = _direct_sql_statement(command)

    if not db_context and not direct:
        return None
    if _looks_like_safe_text_inspection(command, segments) and not direct:
        return None

    if re.search(r"\bdrop\s+table\b", sql, re.I):
        return BlockDecision(
            "sql-drop-table",
            "Blocked `DROP TABLE`. This permanently removes a database table.",
        )
    if re.search(r"\btruncate(?:\s+table)?\b", sql, re.I):
        return BlockDecision(
            "sql-truncate",
            "Blocked SQL `TRUNCATE`. This removes all rows from a table and is often irreversible.",
        )

    for statement in _split_sql_statements(sql):
        if re.search(r"\bdelete\s+from\b", statement, re.I):
            if not re.search(r"\bwhere\b", statement, re.I):
                return BlockDecision(
                    "sql-delete-without-where",
                    "Blocked SQL `DELETE FROM` without a WHERE clause. This can delete every row in the table.",
                )
    return None


def detect_dangerous_command(command: str) -> BlockDecision | None:
    for fragment in _command_substitution_fragments(command):
        if decision := detect_dangerous_command(fragment):
            return decision

    tokens = _tokenize(command)
    segments = _segments(tokens)
    if decision := _detect_rm_rf(segments):
        return decision
    if decision := _detect_git_force_push(segments):
        return decision
    if decision := _detect_sql_destructive(command, segments):
        return decision
    return None


def _log_block(command: str, cwd: str, decision: BlockDecision) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "command": command,
        "project_path": cwd,
        "rule": decision.rule,
        "reason": decision.reason,
    }
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _deny_payload(decision: BlockDecision, command: str) -> dict[str, Any]:
    reason = (
        f"{decision.reason}\n\n"
        f"Command blocked by {HOOK_NAME}: `{command}`\n"
        f"The blocked attempt was logged to {LOG_PATH}."
    )
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def run_hook(input_data: dict[str, Any]) -> dict[str, Any] | None:
    if input_data.get("hook_event_name") != "PreToolUse":
        return None
    if input_data.get("tool_name") != "Bash":
        return None
    tool_input = input_data.get("tool_input") or {}
    command = str(tool_input.get("command") or "")
    if not command.strip():
        return None
    decision = detect_dangerous_command(command)
    if not decision:
        return None
    cwd = str(input_data.get("cwd") or os.getcwd())
    _log_block(command, cwd, decision)
    return _deny_payload(decision, command)


def install_hook() -> None:
    """Install this script and register it in ~/.claude/settings.json."""
    HOOK_INSTALL_PATH.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve()
    if source != HOOK_INSTALL_PATH:
        HOOK_INSTALL_PATH.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        HOOK_INSTALL_PATH.chmod(0o755)
    else:
        source.chmod(0o755)

    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Refusing to modify invalid JSON settings file: {SETTINGS_PATH}: {exc}") from exc
    else:
        settings = {}

    hooks = settings.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    command = f"python3 {HOOK_INSTALL_PATH}"
    entry = {"matcher": "Bash", "hooks": [{"type": "command", "command": command}]}

    def same_hook(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        for hook in item.get("hooks", []):
            if isinstance(hook, dict) and hook.get("command") == command:
                return True
        return False

    if not any(same_hook(item) for item in pre_tool_use):
        pre_tool_use.append(entry)

    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Installed {HOOK_NAME} at {HOOK_INSTALL_PATH}")
    print(f"Registered PreToolUse Bash hook in {SETTINGS_PATH}")


def _read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        # Fail open on malformed hook input so the hook never bricks Claude Code.
        print(f"{HOOK_NAME}: invalid JSON input ignored: {exc}", file=sys.stderr)
        return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claude Code destructive Bash command guard")
    parser.add_argument("--install", action="store_true", help="install and register the hook in ~/.claude/settings.json")
    parser.add_argument("--check", metavar="COMMAND", help="print whether a command would be blocked")
    args = parser.parse_args(argv)

    if args.install:
        install_hook()
        return 0
    if args.check is not None:
        decision = detect_dangerous_command(args.check)
        if decision:
            print(f"BLOCK {decision.rule}: {decision.reason}")
            return 2
        print("ALLOW")
        return 0

    output = run_hook(_read_stdin_json())
    if output:
        print(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
