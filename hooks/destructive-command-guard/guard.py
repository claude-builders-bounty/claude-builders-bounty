#!/usr/bin/env python3
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"

DANGEROUS_PATTERNS = [
    {
        "name": "Recursive Force Removal",
        "regex": r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+|--recursive\s+|--force\s+)+",
        "description": "Destructive file removal ('rm -rf' or equivalent recursive/force flags)."
    },
    {
        "name": "Forced Git Push",
        "regex": r"\bgit\s+push\b.*?(?:--force|-f\b|--force-with-lease)",
        "description": "Forced git push ('git push --force' / '-f') that can overwrite remote history."
    },
    {
        "name": "SQL Drop Table",
        "regex": r"\bDROP\s+TABLE\b",
        "description": "SQL 'DROP TABLE' statement that destroys table structure and data."
    },
    {
        "name": "SQL Truncate",
        "regex": r"\bTRUNCATE(?:\s+TABLE)?\b",
        "description": "SQL 'TRUNCATE' statement that purges all table records."
    },
    {
        "name": "Unbounded SQL Delete",
        "regex": r"\bDELETE\s+FROM\s+[a-zA-Z0-9_.\"']+(?!\s+WHERE\b)",
        "description": "SQL 'DELETE FROM' without a WHERE clause that wipes entire tables."
    }
]


def split_subcommands(command_line: str) -> list[list[str]]:
    # Split by shell command separators: ;, &&, ||, |, &
    subcmd_strings = re.split(r"(?:&&|\|\||;|\||&)", command_line)
    result = []
    for sc in subcmd_strings:
        sc = sc.strip()
        if not sc:
            continue
        try:
            tokens = shlex.split(sc)
        except ValueError:
            tokens = sc.split()
        if tokens:
            result.append(tokens)
    return result


def check_command(command: str) -> dict | None:
    subcommands = split_subcommands(command)

    for tokens in subcommands:
        if not tokens:
            continue

        # Skip common shell wrappers (sudo, doas, nohup, env, etc.)
        idx = 0
        while idx < len(tokens) and tokens[idx] in ("sudo", "doas", "nohup", "env", "command", "builtin"):
            idx += 1

        if idx >= len(tokens):
            continue

        cmd_name = os.path.basename(tokens[idx])
        args = tokens[idx + 1:]

        # Check rm
        if cmd_name in ("rm", "unlink"):
            has_r = any(
                t in ("-r", "-R", "--recursive") or
                (t.startswith("-") and not t.startswith("--") and ("r" in t or "R" in t))
                for t in args
            )
            has_f = any(
                t in ("-f", "--force") or
                (t.startswith("-") and not t.startswith("--") and "f" in t)
                for t in args
            )
            if has_r and has_f:
                return {
                    "name": "Recursive Force Removal",
                    "description": "Destructive file removal ('rm -rf' or equivalent recursive/force flags)."
                }

        # Check git push --force / -f
        if cmd_name == "git" and len(args) > 0 and args[0] == "push":
            push_args = args[1:]
            if any(t in ("-f", "--force", "--force-with-lease") or (t.startswith("-") and not t.startswith("--") and "f" in t) for t in push_args):
                return {
                    "name": "Forced Git Push",
                    "description": "Forced git push ('git push --force' / '-f') that can overwrite remote history."
                }

        # Check SQL commands inside arguments or subcommands
        joined_sub = " ".join(tokens)
        if re.search(r"\bDROP\s+TABLE\b", joined_sub, re.IGNORECASE):
            return {
                "name": "SQL Drop Table",
                "description": "SQL 'DROP TABLE' statement that destroys table structure and data."
            }

        if re.search(r"\bTRUNCATE(?:\s+TABLE)?\b", joined_sub, re.IGNORECASE):
            return {
                "name": "SQL Truncate",
                "description": "SQL 'TRUNCATE' statement that purges all table records."
            }

        if re.search(r"\bDELETE\s+FROM\b", joined_sub, re.IGNORECASE):
            if not re.search(r"\bWHERE\b", joined_sub, re.IGNORECASE):
                return {
                    "name": "Unbounded SQL Delete",
                    "description": "SQL 'DELETE FROM' without a WHERE clause that wipes entire tables."
                }

    return None


def log_blocked(command: str, cwd: str, reason: str) -> None:
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"[{timestamp}] BLOCKED ({reason}) | cwd: {cwd} | command: {command.strip()}\n"
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as err:
        sys.stderr.write(f"Warning: Failed to write to blocked log: {err}\n")


def extract_command() -> tuple[str | None, str]:
    cwd = os.getcwd()
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]), cwd

    if not sys.stdin.isatty():
        raw = sys.stdin.read()
        if not raw.strip():
            return None, cwd
        try:
            payload = json.loads(raw)
            if isinstance(payload, dict):
                cwd = payload.get("cwd", cwd)
                tool = payload.get("tool", "")
                tool_input = payload.get("input", {})
                if tool.lower() == "bash" and isinstance(tool_input, dict):
                    return tool_input.get("command"), cwd
                if "command" in payload:
                    return payload["command"], cwd
        except json.JSONDecodeError:
            return raw.strip(), cwd

    return None, cwd


def main() -> None:
    command, cwd = extract_command()
    if not command:
        sys.exit(0)

    violation = check_command(command)
    if violation:
        log_blocked(command, cwd, violation["name"])
        sys.stderr.write(
            f"\n[SECURITY BLOCK] Command execution denied by Claude Code pre-tool-use guard.\n"
            f"Rule: {violation['name']}\n"
            f"Details: {violation['description']}\n"
            f"Blocked command: {command}\n"
            f"Audit log updated: {LOG_FILE}\n\n"
        )
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
