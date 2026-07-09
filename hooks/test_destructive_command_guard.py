#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HOOK = ROOT / "destructive-command-guard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_payload(payload: object, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={"HOME": str(home), "PATH": ""},
        check=False,
    )


def run_hook(command: str, home: Path) -> subprocess.CompletedProcess[str]:
    return run_payload({
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }, home)


def run_raw_stdin(raw: str, home: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=raw,
        text=True,
        capture_output=True,
        env={"HOME": str(home), "PATH": ""},
        check=False,
    )


def assert_blocked(command: str) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        result = run_hook(command, home)
        assert result.returncode == 2, (command, result.returncode, result.stdout, result.stderr)
        assert "Blocked destructive Bash command" in result.stderr
        log = home / ".claude" / "hooks" / "blocked.log"
        assert log.exists(), command
        entry = json.loads(log.read_text(encoding="utf-8").strip())
        assert entry["attempted_command"] == command
        assert entry["project_path"] == "/tmp/example-project"


def assert_allowed(command: str) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        result = run_hook(command, home)
        assert result.returncode == 0, (command, result.returncode, result.stdout, result.stderr)
        assert result.stderr == ""
        assert not (home / ".claude" / "hooks" / "blocked.log").exists()


def assert_payload_allowed(payload: object) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        result = run_payload(payload, home)
        assert result.returncode == 0, (payload, result.returncode, result.stdout, result.stderr)
        assert result.stderr == ""


def assert_raw_allowed(raw: str) -> None:
    with tempfile.TemporaryDirectory() as d:
        home = Path(d)
        result = run_raw_stdin(raw, home)
        assert result.returncode == 0, (raw, result.returncode, result.stdout, result.stderr)
        assert result.stderr == ""


def main() -> None:
    module = load_module()

    blocked = [
        "rm -rf build",
        "sudo rm -fr /tmp/unsafe",
        "git push --force origin main",
        "git push --force-with-lease",
        "psql -c 'DROP TABLE users'",
        "mysql -e 'TRUNCATE sessions'",
        "psql -c 'DELETE FROM users'",
    ]
    for command in blocked:
        assert_blocked(command)

    allowed = [
        "rm build.log",
        "git push origin main",
        "psql -c 'DELETE FROM users WHERE id = 1'",
        "echo 'rm -rf /tmp/example'",
        "python3 -m pytest",
        "npm test",
    ]
    for command in allowed:
        assert_allowed(command)

    assert_payload_allowed({"tool_name": "Read", "tool_input": {"file_path": "README.md"}})
    assert_payload_allowed({"tool_name": "Bash", "tool_input": {"command": ""}})
    assert_payload_allowed({"tool_input": {"command": "npm test"}})
    assert_raw_allowed("{not json")
    assert_raw_allowed("")

    assert module.blocked_reason("DELETE FROM users WHERE id = 1") is None
    assert module.blocked_reason("DELETE FROM users; SELECT 1") is not None
    print("destructive-command-guard: all tests passed")


if __name__ == "__main__":
    main()
