#!/usr/bin/env python3
"""
Claude Code PreToolUse Hook: Destructive Bash Command Blocker

Intercepts dangerous bash commands before execution and rejects them with
exit code 2 (Claude Code hook convention), printing a clear explanation.
Every blocked attempt is logged to ~/.claude/hooks/blocked.log.

Blocks:
  - `rm -rf` (recursive force removals of files/directories)
  - `DROP TABLE` (and other DROP DDL statements: DATABASE, SCHEMA, VIEW, INDEX)
  - `git push --force` (including `-f`, `+<ref>`)
  - `TRUNCATE` (TRUNCATE TABLE / TRUNCATE)
  - `DELETE FROM` without a WHERE clause

Pure Python 3 stdlib — zero external dependencies.
"""

import sys
import os
import json
import re
import shlex
from datetime import datetime, timezone
from pathlib import Path

HOOKS_DIR = Path(os.environ.get("CLAUDE_HOOKS_DIR", Path.home() / ".claude" / "hooks"))
LOG_FILE = Path(os.environ.get("CLAUDE_GUARD_LOG", HOOKS_DIR / "blocked.log"))

# SQL / DB commands
DB_CLIENTS = {
    "psql", "mysql", "mariadb", "sqlite3", "sqlite", "mongo", "mongosh", "redis-cli",
    "cockroach", "clickhouse-client", "clickhouse", "snowsql", "bq", "sqlcmd", "duckdb",
    "pgcli", "mycli", "mysqlsh",
}

QUOTED_RE = re.compile(r"'[^']*'|\"[^\"]*\"")

def _segments(command: str):
    """Splits compound commands (&&, ||, ;, newlines) into individual segments while respecting quotes."""
    parts = []
    current = []
    in_single = False
    in_double = False
    i = 0
    while i < len(command):
        c = command[i]
        if c == "'" and not in_double:
            in_single = not in_single
            current.append(c)
        elif c == '"' and not in_single:
            in_double = not in_double
            current.append(c)
        elif not in_single and not in_double:
            if command[i:i+2] in ('&&', '||'):
                parts.append(''.join(current).strip())
                current = []
                i += 1
            elif c in (';', '\n'):
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(c)
        else:
            current.append(c)
        i += 1
    if current:
        parts.append(''.join(current).strip())
    return [p for p in parts if p]

def _tokens(segment: str):
    """Tokenizes a shell command safely."""
    try:
        return shlex.split(segment)
    except ValueError:
        return segment.split()

def check_rm_rf(command: str):
    """
    Checks if a command contains rm with recursive (-r, -R) AND force (-f, -F) flags.
    Blocks any rm -rf invocation as strictly requested by the bounty acceptance criteria.
    """
    for segment in _segments(command):
        toks = _tokens(segment)
        idx = next((i for i, t in enumerate(toks) if t == "rm" or t.endswith("/rm")), None)
        if idx is None:
            continue
        args = toks[idx + 1:]
        flags = [a for a in args if a.startswith("-")]
        combined_flags = "".join(f.lstrip("-") for f in flags)
        
        has_r = ("r" in combined_flags or "R" in combined_flags or "--recursive" in flags)
        has_f = ("f" in combined_flags or "F" in combined_flags or "--force" in flags)
        
        if has_r and has_f:
            return True, "rm-rf", "Recursive force removal (`rm -rf`) can cause irreversible data loss."
    return False, "", ""

def _sql_surfaces(command: str):
    """
    Extracts text to inspect for SQL rules.
    Inspects bare SQL directly, and inspects quoted strings if executed by a DB CLI tool.
    E.g.: `psql -c "DROP TABLE users"` -> inspected.
          `echo "DROP TABLE users"` -> not treated as active SQL execution.
    """
    surfaces = [QUOTED_RE.sub(" ", command)]
    for segment in _segments(command):
        toks = _tokens(segment)
        if toks and any(client in os.path.basename(toks[0]) for client in DB_CLIENTS):
            surfaces.extend(q.strip("'\"") for q in QUOTED_RE.findall(segment))
    return surfaces

def check_drop(command: str):
    for surface in _sql_surfaces(command):
        m = re.search(r"\bDROP\s+(TABLE|DATABASE|SCHEMA|VIEW|INDEX)\b", surface, re.IGNORECASE)
        if m:
            return True, "sql-drop", f"SQL statement `DROP {m.group(1).upper()}` detected. Dropping entities causes permanent schema and data loss."
    return False, "", ""

def check_truncate(command: str):
    for surface in _sql_surfaces(command):
        m = re.search(r"\bTRUNCATE(?:\s+TABLE)?\s+([\w\.\"`']+)", surface, re.IGNORECASE)
        if m:
            entity = m.group(1)
            return True, "sql-truncate", f"SQL statement `TRUNCATE TABLE {entity}` detected. Truncating tables deletes all records permanently."
    return False, "", ""

def check_delete_without_where(command: str):
    for surface in _sql_surfaces(command):
        for stmt in re.split(r";", surface):
            if not re.search(r"\bDELETE\s+FROM\b", stmt, re.IGNORECASE):
                continue
            if not re.search(r"\bWHERE\b", stmt, re.IGNORECASE):
                m = re.search(r"\bDELETE\s+FROM\s+([\w\.\"`']+)", stmt, re.IGNORECASE)
                table_name = m.group(1) if m else "target table"
                return True, "sql-delete-no-where", f"SQL statement `DELETE FROM {table_name}` without a WHERE clause detected. This deletes all records."
    return False, "", ""

def check_git_force_push(command: str):
    for segment in _segments(command):
        if not re.search(r"\bgit\s+(?:[^\n;&|`]*?\s+)?push\b", segment, re.IGNORECASE):
            continue
        if re.search(r"--force\b", segment, re.IGNORECASE) or re.search(r"(?:^|\s)-[a-zA-Z0-9]*f\b", segment) or re.search(r"\+[a-zA-Z0-9_\-\.\/]+:[a-zA-Z0-9_\-\.\/]+", segment):
            return True, "git-force-push", "Git force push detected (`git push --force` or `-f`). This can rewrite remote history and erase teammate commits."
    return False, "", ""

def check_destructive_command(command: str):
    """
    Evaluates whether the bash command contains any blocked destructive patterns.
    Returns (is_blocked: bool, rule_name: str, explanation: str).
    """
    clean_cmd = command.strip()
    if not clean_cmd:
        return False, "", ""

    # 1. rm -rf
    blocked, rule, expl = check_rm_rf(clean_cmd)
    if blocked:
        return True, rule, expl

    # 2. DROP TABLE / DATABASE / etc.
    blocked, rule, expl = check_drop(clean_cmd)
    if blocked:
        return True, rule, expl

    # 3. TRUNCATE
    blocked, rule, expl = check_truncate(clean_cmd)
    if blocked:
        return True, rule, expl

    # 4. DELETE FROM without WHERE clause
    blocked, rule, expl = check_delete_without_where(clean_cmd)
    if blocked:
        return True, rule, expl

    # 5. git push --force
    blocked, rule, expl = check_git_force_push(clean_cmd)
    if blocked:
        return True, rule, expl

    return False, "", ""

def log_blocked(command: str, project_path: str, reason: str):
    """Logs the blocked command attempt to ~/.claude/hooks/blocked.log with ISO-8601 UTC timestamp, command, and path."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = {
            "timestamp": timestamp,
            "project_path": project_path,
            "command": " ".join(command.split()),
            "reason": reason
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        sys.stderr.write(f"Warning: Failed to log blocked command: {e}\n")

def main():
    raw_input_data = ""
    try:
        if not sys.stdin.isatty():
            raw_input_data = sys.stdin.read()
    except Exception:
        pass

    command = ""
    project_path = os.getcwd()

    if raw_input_data.strip():
        try:
            payload = json.loads(raw_input_data)
            tool_input = payload.get("tool_input", {})
            if isinstance(tool_input, dict):
                command = tool_input.get("command", "")
            if not command and "command" in payload:
                command = payload.get("command", "")
            if "project_path" in payload:
                project_path = payload["project_path"]
            elif "cwd" in payload:
                project_path = payload["cwd"]
        except json.JSONDecodeError:
            command = raw_input_data.strip()

    if not command and len(sys.argv) > 1:
        command = " ".join(sys.argv[1:])

    if not command:
        sys.exit(0)

    is_blocked, rule_name, explanation = check_destructive_command(command)

    if is_blocked:
        log_blocked(command, project_path, rule_name)
        message = (
            f"\n🚨 [BLOCKED BY SECURITY HOOK] Destructive bash command intercepted!\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Rule Triggered : {rule_name}\n"
            f"Attempted Cmd  : {command}\n"
            f"Project Path   : {project_path}\n"
            f"Reason         : {explanation}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Action: If you really need to perform this operation, run it manually or rewrite it safely (e.g., add WHERE clause to SQL, avoid force push, target specific files).\n"
        )
        sys.stderr.write(message)
        # Claude Code PreToolUse hook contract: exit 2 blocks command execution
        sys.exit(2)

    sys.exit(0)

if __name__ == "__main__":
    main()
