#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook (`~/.claude/hooks/pre_tool_use.py`)
Bounty Reference: claude-builders-bounty/claude-builders-bounty#3 ($100 Opire)

Supports:
1. Claude Code PreToolUse stdin JSON payload (`{"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}`)
   - Outputs JSON `{"decision": "block", "reason": "..."}` and exits with code 2 on blocked commands.
   - Logs every blocked attempt to `~/.claude/hooks/blocked.log` (timestamp, attempted command, project path).
2. Direct CLI command argument (`python3 pre_tool_use.py "rm -rf /tmp/x"`)
3. Built-in self-test suite (`python3 pre_tool_use.py --test` or when run interactively with no args).
"""
import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

PATTERNS = [
    (
        re.compile(r"\brm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+)*-[a-zA-Z]*[rf][a-zA-Z]*|\brm\s+--(?:recursive|force)\b", re.I),
        "Destructive recursive/force deletion (rm -rf) is prohibited.",
    ),
    (
        re.compile(r"\bDROP\s+TABLE\b", re.I),
        "SQL DROP TABLE is prohibited by pre-tool-use security policy.",
    ),
    (
        re.compile(r"\bgit\s+push\b.*?(?:--force(?:-with-lease)?\b|-f\b)", re.I),
        "Force pushing (git push --force) is prohibited.",
    ),
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?[\w.`\"']+", re.I),
        "SQL TRUNCATE is prohibited by pre-tool-use security policy.",
    ),
]
DELETE_WHERE_RE = re.compile(r"\bDELETE\s+FROM\s+[\w.`\"']+(?!\s+WHERE\b)", re.I)


def evaluate_command(command: str, project_path: str = "", log_path: Optional[Path] = None) -> dict:
    cmd = (command or "").strip()
    reason = None

    # Check rm -rf specifically (both -rf/-fr combined and separate -r -f flags)
    if re.search(r"\brm\b", cmd, re.I):
        if re.search(r"\s-[a-zA-Z]*r[a-zA-Z]*f|\s-[a-zA-Z]*f[a-zA-Z]*r|(\s-r\b.*?\s-f\b)|(\s-f\b.*?\s-r\b)", cmd, re.I):
            reason = "Destructive recursive force deletion (rm -rf) is prohibited."

    if not reason:
        for rx, msg in PATTERNS[1:]:
            if rx.search(cmd):
                reason = msg
                break

    if not reason and re.search(r"\bDELETE\s+FROM\b", cmd, re.I):
        if not re.search(r"\bDELETE\s+FROM\s+[\w.`\"']+\s+WHERE\s+\S+", cmd, re.I):
            reason = "SQL DELETE FROM without an explicit WHERE clause is prohibited."

    if reason:
        target_log = log_path or (Path.home() / ".claude" / "hooks" / "blocked.log")
        target_log.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().astimezone().isoformat()
        cwd = project_path or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(f"{ts} | project={cwd} | command={cmd} | reason={reason}\n")
        msg = f"Blocked destructive command: {reason} (Attempt logged to {target_log})"
        return {"decision": "block", "reason": msg}

    return {"decision": "approve"}


def run_self_test() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        lp = Path(td) / "blocked.log"
        assert evaluate_command("rm -rf /tmp/build", td, lp)["decision"] == "block"
        assert evaluate_command("rm -fr ./dist", td, lp)["decision"] == "block"
        assert evaluate_command("psql -c 'DROP TABLE users;'", td, lp)["decision"] == "block"
        assert evaluate_command("git push origin main --force", td, lp)["decision"] == "block"
        assert evaluate_command("psql -c 'TRUNCATE TABLE audit_logs;'", td, lp)["decision"] == "block"
        assert evaluate_command("sqlite3 db 'DELETE FROM accounts;'", td, lp)["decision"] == "block"
        assert evaluate_command("sqlite3 db 'DELETE FROM accounts WHERE id = 5;'", td, lp)["decision"] == "approve"
        assert evaluate_command("ls -la && git status", td, lp)["decision"] == "approve"
        assert lp.is_file() and len(lp.read_text().splitlines()) == 6
    print("ALL_6_ACCEPTANCE_CRITERIA_TESTS_PASSED")


def main() -> int:
    if "--test" in sys.argv:
        run_self_test()
        return 0

    raw_stdin = ""
    if not sys.stdin.isatty():
        raw_stdin = sys.stdin.read().strip()

    if not raw_stdin and len(sys.argv) > 1:
        res = evaluate_command(" ".join(sys.argv[1:]))
        print(json.dumps(res))
        if res["decision"] == "block":
            print(res["reason"], file=sys.stderr)
            return 2
        return 0

    if not raw_stdin:
        run_self_test()
        return 0

    try:
        payload = json.loads(raw_stdin)
        tool_input = payload.get("tool_input") or payload.get("input") or {}
        command = (
            tool_input.get("command")
            or payload.get("command")
            or (raw_stdin if isinstance(tool_input, str) else "")
        )
        project_path = payload.get("cwd") or payload.get("project_path") or os.getcwd()
    except Exception:
        command = raw_stdin
        project_path = os.getcwd()

    res = evaluate_command(command, project_path=project_path)
    print(json.dumps(res))
    if res["decision"] == "block":
        print(res["reason"], file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
