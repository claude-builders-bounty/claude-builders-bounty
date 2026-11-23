#!/usr/bin/env python3
"""
Claude Code Pre-Tool-Use Security Hook (`~/.claude/hooks/pre_tool_use.py`)
Bounty Reference: claude-builders-bounty/claude-builders-bounty#3 ($100 Opire)
"""
import os, re, sys, json
from datetime import datetime
from pathlib import Path

PATTERNS = [
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", re.I), "Destructive recursive force deletion (rm -rf) is prohibited."),
    (re.compile(r"\bDROP\s+TABLE\b", re.I), "SQL DROP TABLE is prohibited by pre-tool-use security policy."),
    (re.compile(r"\bgit\s+push\b.*?(?:--force\b|-f\b)", re.I), "Force pushing (git push --force) is prohibited."),
    (re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?\w+", re.I), "SQL TRUNCATE is prohibited."),
]
DELETE_RE = re.compile(r"\bDELETE\s+FROM\s+[\w.`\"']+(?:\s*;|$)", re.I)

def evaluate_command(command: str, project_path: str = "", log_path: Path = None) -> dict:
    reason = None
    for rx, msg in PATTERNS:
        if rx.search(command or ""):
            reason = msg
            break
    if not reason and "delete from" in (command or "").lower():
        if "where " not in (command or "").lower() or DELETE_RE.search(command or ""):
            reason = "SQL DELETE FROM without an explicit WHERE clause is prohibited."
    if reason:
        target_log = log_path or (Path.home() / ".claude" / "hooks" / "blocked.log")
        target_log.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().astimezone().isoformat()
        cwd = project_path or os.getcwd()
        with open(target_log, "a", encoding="utf-8") as f:
            f.write(f"{ts} | project={cwd} | blocked_command={command!r} | reason={reason}\n")
        return {"decision": "block", "reason": f"[SECURITY HOOK BLOCKED] {reason}"}
    return {"decision": "approve"}

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        lp = Path(td) / "blocked.log"
        assert evaluate_command("rm -rf /tmp/build", td, lp)["decision"] == "block"
        assert evaluate_command("psql -c 'DROP TABLE users;'", td, lp)["decision"] == "block"
        assert evaluate_command("git push origin main --force", td, lp)["decision"] == "block"
        assert evaluate_command("sqlite3 db 'DELETE FROM accounts;'", td, lp)["decision"] == "block"
        assert evaluate_command("sqlite3 db 'DELETE FROM accounts WHERE id = 5;'", td, lp)["decision"] == "approve"
        assert evaluate_command("ls -la && git status", td, lp)["decision"] == "approve"
        assert lp.is_file() and len(lp.read_text().splitlines()) == 4
    print("ALL_6_ACCEPTANCE_CRITERIA_TESTS_PASSED")
