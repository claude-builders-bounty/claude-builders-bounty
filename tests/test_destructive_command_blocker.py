#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive-command-blocker" / "pre-tool-use"


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(ROOT),
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, tmp_home: Path) -> None:
    result = run_hook(command, tmp_home)
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    decision = out["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert "Blocked destructive Bash command" in decision["permissionDecisionReason"]


def assert_allowed(command: str, tmp_home: Path) -> None:
    result = run_hook(command, tmp_home)
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def main() -> None:
    tmp_home = ROOT / ".tmp-hook-test-home"
    if tmp_home.exists():
        for path in sorted(tmp_home.rglob("*"), reverse=True):
            path.unlink() if path.is_file() else path.rmdir()
    tmp_home.mkdir(exist_ok=True)

    blocked = [
        "rm -rf /tmp/build",
        "sudo rm -rf /var/tmp/build",
        "git push --force origin main",
        "git push -f origin main",
        "psql -c 'DROP TABLE users'",
        "mysql -e 'TRUNCATE audit_log'",
        "sqlite3 app.db 'DELETE FROM sessions'",
    ]
    for command in blocked:
        assert_blocked(command, tmp_home)

    allowed = [
        "rm build.log",
        "git push origin main",
        "sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < datetime(\"now\")'",
        "python3 -m pytest",
    ]
    for command in allowed:
        assert_allowed(command, tmp_home)

    log_file = tmp_home / ".claude" / "hooks" / "blocked.log"
    log_text = log_file.read_text(encoding="utf-8")
    assert log_text.count("command=") == len(blocked)
    assert f"project={ROOT}" in log_text
    print("All hook tests passed.")


if __name__ == "__main__":
    main()
