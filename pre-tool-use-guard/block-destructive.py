#!/usr/bin/env python3
"""PreToolUse guard for Claude Code: blocks destructive shell commands.

Reads the Claude Code hook payload from stdin, inspects `tool_input.command`
and exits with code 2 (block + explain) when the command would recursively force
delete files, rewrite git history, or run an unguarded destructive SQL statement.

Exit codes:
    0  allow (also used when the payload is unreadable -- the guard fails open)
    2  block; stderr is shown to Claude as the reason

Commands:
    block-destructive.py --install     merge the hook into ~/.claude/settings.json
    block-destructive.py --uninstall   remove it again
    block-destructive.py --check "rm -rf /"   dry-run: print the verdict

Environment:
    CLAUDE_ALLOW_DESTRUCTIVE=1   bypass the guard for this session (logged)
    CLAUDE_HOOK_LOG=/path/file   override the log location (tests)

Requires Python 3.8+. Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

ALLOW_ENV = "CLAUDE_ALLOW_DESTRUCTIVE"
LOG_ENV = "CLAUDE_HOOK_LOG"
MAX_LOG_BYTES = 5 * 1024 * 1024
MAX_DEPTH = 4

SQL_CLIENTS = {
    "psql",
    "mysql",
    "mariadb",
    "sqlite3",
    "sqlite",
    "turso",
    "libsql",
    "duckdb",
    "clickhouse-client",
    "mongosh",
    "mongo",
}

SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish"}

# Prefixes that do not change what actually runs.
WRAPPERS = {
    "sudo",
    "doas",
    "env",
    "time",
    "nice",
    "nohup",
    "command",
    "exec",
    "stdbuf",
    "unbuffer",
    "xargs",
    "builtin",
    "then",
    "do",
    "else",
    "if",
    "while",
    "until",
    "!",
    "{",
    "(",
}

ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


@dataclass(frozen=True)
class Decision:
    rule: str
    reason: str
    hint: str

    def message(self, command: str) -> str:
        return (
            f"BLOCKED by pre-tool-use hook ({self.rule}).\n"
            f"Command: {command.strip()}\n\n"
            f"Why: {self.reason}\n\n"
            f"What to do instead: {self.hint}\n"
            f"If the user explicitly approved this exact action, ask them to run it "
            f"themselves, or set {ALLOW_ENV}=1 for this session."
        )


def _rule_rm(tokens: list[str]) -> Decision | None:
    recursive = force = False
    for arg in tokens:
        if arg == "--":
            break
        if arg.startswith("--"):
            if arg == "--recursive":
                recursive = True
            elif arg == "--force":
                force = True
        elif arg.startswith("-") and len(arg) > 1:
            flags = arg[1:]
            if "r" in flags or "R" in flags:
                recursive = True
            if "f" in flags:
                force = True
    if recursive and force:
        return Decision(
            rule="rm_rf",
            reason=(
                "recursive + force delete is unrecoverable and almost always wider than "
                "intended: a mistyped path, an unset variable or a missing slash turns "
                "`rm -rf $DIR/` into `rm -rf /`."
            ),
            hint=(
                "delete known files explicitly (`rm file1 file2`), or use `rm -r` without "
                "`-f` so the shell asks before removing write-protected paths; for build "
                "artifacts prefer the project's own clean task."
            ),
        )
    return None


def _rule_git(tokens: list[str]) -> Decision | None:
    if "push" not in tokens[1:]:
        return None
    force_flags = {"-f", "--force", "--force-with-lease", "--force-if-includes"}
    for arg in tokens[1:]:
        if arg in force_flags or (arg.startswith("+") and len(arg) > 1):
            return Decision(
                rule="git_push_force",
                reason=(
                    "a forced push rewrites remote history. Commits that other people "
                    "already pulled disappear, and the only copy may be a local reflog."
                ),
                hint=(
                    "push a new commit or a branch instead. If history really must be "
                    "rewritten, use `--force-with-lease` manually after confirming the "
                    "remote ref has not moved, and never on a shared branch such as main."
                ),
            )
    return None


DELETE_FROM = re.compile(r"\bdelete\s+from\b", re.IGNORECASE)
WHERE = re.compile(r"\bwhere\b", re.IGNORECASE)
DROP_TABLE = re.compile(r"\bdrop\s+table\b", re.IGNORECASE)
DROP_DATABASE = re.compile(r"\bdrop\s+(?:database|schema)\b", re.IGNORECASE)
TRUNCATE = re.compile(r"\btruncate\s+(?:table\s+)?[\w\"`\[.]", re.IGNORECASE)


def _rule_sql(text: str) -> Decision | None:
    if DROP_TABLE.search(text):
        return Decision(
            rule="sql_drop_table",
            reason=(
                "DROP TABLE destroys the table and its rows in one statement. There is no "
                "transaction to roll back once it commits, and migrations may immediately "
                "recreate an empty table that looks correct."
            ),
            hint=(
                "write a migration instead: create a new table, copy the data, verify, then "
                "drop the old one in a separate reviewed migration. For a local scratch "
                "database, recreate it from seed data."
            ),
        )
    if DROP_DATABASE.search(text):
        return Decision(
            rule="sql_drop_database",
            reason="dropping a database or schema removes every table in it, not just one object.",
            hint="drop individual tables through a reviewed migration, after taking a backup.",
        )
    if TRUNCATE.search(text):
        return Decision(
            rule="sql_truncate",
            reason=(
                "TRUNCATE empties a whole table without a WHERE clause and, unlike DELETE, "
                "usually cannot be undone by a transaction rollback."
            ),
            hint="delete the specific rows with a WHERE clause, or run it against a scratch database.",
        )
    for statement in text.split(";"):
        if DELETE_FROM.search(statement) and not WHERE.search(statement):
            return Decision(
                rule="sql_delete_without_where",
                reason=(
                    "DELETE without a WHERE clause removes every row in the table. It is a "
                    "single keystroke away from a full data loss and rarely what was intended."
                ),
                hint=(
                    "add a WHERE clause, or run `SELECT count(*)` with the same predicate "
                    "first to confirm the number of affected rows."
                ),
            )
    return None


def _strip_prefixes(tokens: list[str]) -> list[str]:
    """Drop sudo/env/time/nohup wrappers, their flags and VAR=value assignments."""
    i = 0
    while i < len(tokens):
        token = tokens[i]
        base = os.path.basename(token).lower()
        if base in WRAPPERS or ENV_ASSIGNMENT.match(token) or token.startswith("-"):
            i += 1
            # `sudo -u root cmd` and `env -i cmd`: skip the flag's value when it is not a flag
            if (
                token in {"-u", "-g", "-C", "-n", "-p", "-U", "--user", "--group"}
                and i < len(tokens)
            ):
                i += 1
            continue
        break
    return tokens[i:]


def _analyze_tokens(tokens: list[str], depth: int) -> Decision | None:
    tokens = _strip_prefixes(tokens)
    if not tokens:
        return None

    program = os.path.basename(tokens[0]).lower()
    args = tokens[1:]

    if program == "rm":
        return _rule_rm(args)
    if program == "git":
        return _rule_git(tokens)
    if program in SQL_CLIENTS:
        return _rule_sql(" ".join(args))

    if program in SHELLS:
        for i, arg in enumerate(args):
            if arg == "-c" and i + 1 < len(args):
                return _analyze_command(args[i + 1], depth + 1)

    if program == "eval" and args:
        return _analyze_command(" ".join(args), depth + 1)

    return None


def _analyze_command(command: str, depth: int = 0) -> Decision | None:
    if depth > MAX_DEPTH or not command.strip():
        return None
    try:
        tokens = shlex.split(command, comments=False, posix=True)
    except ValueError:
        tokens = command.split()
    return _analyze_tokens(tokens, depth)


def split_segments(command: str) -> list[str]:
    """Split on ; && || | newlines, ignoring separators inside quotes."""
    segments: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    while i < len(command):
        char = command[i]
        if quote:
            buf.append(char)
            if char == "\\" and quote == '"' and i + 1 < len(command):
                buf.append(command[i + 1])
                i += 2
                continue
            if char == quote:
                quote = None
            i += 1
            continue
        if char in "'\"`":
            quote = char
            buf.append(char)
            i += 1
            continue
        if command.startswith("&&", i) or command.startswith("||", i):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if char in ";\n|":
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(char)
        i += 1
    segments.append("".join(buf))
    return [s.strip() for s in segments if s.strip()]


def evaluate(command: str) -> Decision | None:
    """Return the blocking Decision for a command line, or None to allow it."""
    for segment in split_segments(command):
        decision = _analyze_command(segment)
        if decision:
            return decision
    return None


def log_path() -> Path:
    override = os.environ.get(LOG_ENV)
    if override:
        return Path(override).expanduser()
    return Path.home() / ".claude" / "hooks" / "blocked.log"


def log_block(decision: Decision, command: str, payload: dict, bypassed: bool = False) -> None:
    path = log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > MAX_LOG_BYTES:
            path.replace(path.with_name(path.name + ".1"))
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "decision": "bypassed" if bypassed else "blocked",
            "rule": decision.rule,
            "command": command,
            "project": str(payload.get("cwd") or os.getcwd()),
            "session_id": payload.get("session_id", ""),
            "tool": payload.get("tool_name", ""),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Never fail the guard because the log is not writable.
        pass


def settings_path() -> Path:
    return Path.home() / ".claude" / "settings.json"


def install() -> int:
    hook_dir = Path.home() / ".claude" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    target = hook_dir / "block-destructive.py"
    source = Path(__file__).resolve()
    if target.resolve() != source:
        shutil.copy2(source, target)

    path = settings_path()
    data: dict = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Cannot parse {path}; fix it manually and re-run --install.", file=sys.stderr)
            return 1

    hooks = data.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])
    if not isinstance(pre_tool_use, list):
        print(f"{path}: hooks.PreToolUse is not a list; fix it manually.", file=sys.stderr)
        return 1

    command = f'"{sys.executable}" "{target}"'
    for group in pre_tool_use:
        for hook in (group or {}).get("hooks", []) if isinstance(group, dict) else []:
            if "block-destructive.py" in str(hook.get("command", "")):
                print("Hook is already installed.")
                return 0

    pre_tool_use.append(
        {
            "matcher": "Bash",
            "hooks": [{"type": "command", "command": command, "timeout": 10}],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Installed into {path}")
    print("Restart Claude Code to load the hook.")
    return 0


def uninstall() -> int:
    path = settings_path()
    if not path.exists():
        print("No settings.json found; nothing to remove.")
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    groups = data.get("hooks", {}).get("PreToolUse", [])
    kept = [
        group
        for group in groups
        if not any(
            "block-destructive.py" in str(hook.get("command", ""))
            for hook in (group or {}).get("hooks", [])
        )
    ]
    data.setdefault("hooks", {})["PreToolUse"] = kept
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Removed from {path}")
    return 0


def main(argv: list[str]) -> int:
    if "--install" in argv:
        return install()
    if "--uninstall" in argv:
        return uninstall()
    if "--check" in argv:
        index = argv.index("--check")
        command = argv[index + 1] if index + 1 < len(argv) else ""
        decision = evaluate(command)
        if decision:
            print(decision.message(command))
            return 2
        print("allowed")
        return 0

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0  # fail open: a malformed payload must not brick the session
    if not isinstance(payload, dict):
        return 0

    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command") or ""
    if not isinstance(command, str) or not command.strip():
        return 0

    decision = evaluate(command)
    if decision is None:
        return 0

    if os.environ.get(ALLOW_ENV, "").lower() in {"1", "true", "yes", "on"}:
        log_block(decision, command, payload, bypassed=True)
        print(
            f"WARNING: destructive command allowed because {ALLOW_ENV} is set: {command.strip()}",
            file=sys.stderr,
        )
        return 0

    log_block(decision, command, payload)
    print(decision.message(command), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
