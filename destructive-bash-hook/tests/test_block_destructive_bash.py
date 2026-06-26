#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block-destructive-bash.py"


spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def assert_blocked(command: str, expected: str) -> None:
    reason = module.blocked_reason(command)
    assert reason is not None, f"expected block for: {command}"
    assert expected.lower() in reason.lower(), f"{reason!r} did not contain {expected!r}"


def assert_allowed(command: str) -> None:
    assert module.blocked_reason(command) is None, f"expected allow for: {command}"


def run_hook(command: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def main() -> None:
    assert_blocked("rm -rf build/", "rm -rf")
    assert_blocked("rm -fr build/", "rm -rf")
    assert_blocked("psql -c 'DROP TABLE users'", "drop table")
    assert_blocked("mysql -e 'TRUNCATE audit_log'", "truncate")
    assert_blocked("git push --force origin main", "force push")
    assert_blocked("git push -f origin main", "force push")
    assert_blocked("psql -c 'DELETE FROM users'", "without a WHERE")

    assert_allowed("rm -r build/")
    assert_allowed("git push origin main")
    assert_allowed("psql -c 'DELETE FROM users WHERE id = 1'")
    assert_allowed("python manage.py test")

    with tempfile.TemporaryDirectory() as home:
        completed = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf tmp/"},
                "cwd": "/tmp/example-project",
            }),
            text=True,
            capture_output=True,
            check=False,
            env={"HOME": home, "USERPROFILE": home},
        )
        assert completed.returncode == 2
        assert "Blocked destructive Bash command" in completed.stderr
        log_file = Path(home) / ".claude" / "hooks" / "blocked.log"
        assert log_file.exists()
        log_entry = json.loads(log_file.read_text(encoding="utf-8").strip())
        assert log_entry["command"] == "rm -rf tmp/"
        assert log_entry["project_path"] == "/tmp/example-project"

    print("All destructive bash hook tests passed.")


if __name__ == "__main__":
    main()

