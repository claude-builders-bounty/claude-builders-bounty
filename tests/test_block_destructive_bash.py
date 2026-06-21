#!/usr/bin/env python3
"""Self-contained tests for .claude/hooks/block-destructive-bash.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block-destructive-bash.py"

DANGEROUS = [
    "rm -rf /tmp/build",
    "rm -fr ./dist",
    "psql -c 'DROP TABLE users'",
    "git push origin main --force",
    "sqlite3 app.db 'TRUNCATE sessions'",
    "mysql -e 'DELETE FROM users'",
    "psql -c 'DELETE FROM accounts;'",
]

SAFE = [
    "echo hello",
    "npm test",
    "rm README.tmp",
    "git push origin main",
    "git push --force-with-lease origin main",
    "sqlite3 app.db 'DELETE FROM users WHERE id = 42'",
    "grep -R 'DROP TABLE' docs/",
]


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(ROOT),
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = str(ROOT)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_denied(result: subprocess.CompletedProcess[str], command: str) -> None:
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip(), f"expected denial JSON for {command!r}"
    data = json.loads(result.stdout)
    output = data["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "Blocked destructive Bash command" in output["permissionDecisionReason"]


def assert_allowed(result: subprocess.CompletedProcess[str], command: str) -> None:
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", f"expected no hook output for safe command {command!r}; got {result.stdout!r}"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        for command in DANGEROUS:
            assert_denied(run_hook(command, home), command)
        for command in SAFE:
            assert_allowed(run_hook(command, home), command)

        log_file = home / ".claude" / "hooks" / "blocked.log"
        assert log_file.exists(), "blocked.log was not created"
        lines = log_file.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == len(DANGEROUS), f"expected {len(DANGEROUS)} log lines, got {len(lines)}"
        for line, command in zip(lines, DANGEROUS):
            record = json.loads(line)
            assert record["timestamp"], record
            assert record["attempted_command"] == command, record
            assert record["project_path"] == str(ROOT), record

    print(f"PASS: blocked {len(DANGEROUS)} dangerous commands and allowed {len(SAFE)} safe commands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
