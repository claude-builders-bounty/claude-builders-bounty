#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre-tool-use.py"
INSTALLER = ROOT / "install.py"


def run_hook(command: str, *, home: Path, cwd: str = "/tmp/project") -> subprocess.CompletedProcess[str]:
    payload = {
        "session_id": "test-session",
        "cwd": cwd,
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


def assert_blocked(command: str, home: Path) -> None:
    result = run_hook(command, home=home)
    assert result.returncode == 2, (command, result.returncode, result.stdout, result.stderr)
    assert "Blocked destructive Bash command" in result.stderr


def assert_allowed(command: str, home: Path) -> None:
    result = run_hook(command, home=home)
    assert result.returncode == 0, (command, result.returncode, result.stdout, result.stderr)
    assert result.stdout == ""
    assert result.stderr == ""


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="hook-bounty-") as raw_home:
        home = Path(raw_home)

        blocked = [
            "rm -rf build",
            "rm -fr build",
            "rm -r -f build",
            "DROP TABLE users;",
            "drop table users;",
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "TRUNCATE TABLE sessions;",
            "truncate sessions;",
            "DELETE FROM users;",
            "delete from users",
            "echo ok && DELETE FROM users",
        ]
        for command in blocked:
            assert_blocked(command, home)

        allowed = [
            "ls -la",
            "git status",
            "rm build.tmp",
            "git push origin feature/test",
            "DELETE FROM users WHERE id = 7;",
            "delete from users where email = 'a@example.com'",
            "python3 -m pytest -q",
        ]
        for command in allowed:
            assert_allowed(command, home)

        log_path = home / ".claude" / "hooks" / "blocked.log"
        records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
        assert len(records) == len(blocked)
        for record, command in zip(records, blocked):
            assert record["command"] == command
            assert record["project_path"] == "/tmp/project"
            assert record["timestamp"].endswith("+00:00")
            assert record["reason"]

        # Malformed hook input must fail closed instead of allowing an unknown Bash call.
        env = os.environ.copy()
        env["HOME"] = str(home)
        env["USERPROFILE"] = str(home)
        malformed = subprocess.run(
            [sys.executable, str(HOOK)],
            input="{not-json",
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
        assert malformed.returncode == 2

        # Installer test uses the same temporary HOME and must preserve unrelated settings.
        claude_dir = home / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        settings_path = claude_dir / "settings.json"
        settings_path.write_text(json.dumps({"theme": "dark", "hooks": {"PostToolUse": []}}), encoding="utf-8")
        for _ in range(2):
            installed = subprocess.run(
                [sys.executable, str(INSTALLER)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            assert installed.returncode == 0, installed.stderr

        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        assert settings["theme"] == "dark"
        assert settings["hooks"]["PostToolUse"] == []
        pre = settings["hooks"]["PreToolUse"]
        assert len(pre) == 1, pre
        assert pre[0]["matcher"] == "Bash"
        handler = pre[0]["hooks"][0]
        assert handler["type"] == "command"
        assert "pre-tool-use.py" in handler["command"]
        installed_hook = home / ".claude" / "hooks" / "pre-tool-use.py"
        assert installed_hook.exists()
        assert installed_hook.read_bytes() == HOOK.read_bytes()

    print("PASS: destructive hook acceptance suite")
    print(f"blocked_cases={len(blocked)} allowed_cases={len(allowed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
