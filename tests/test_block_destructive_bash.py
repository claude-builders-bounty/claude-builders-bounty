#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "pre-tool-use" / "block_destructive_bash.py"


def run(payload, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run([str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, env=env)


def main():
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp)
        base = {"tool_name": "Bash", "cwd": "/repo", "tool_input": {"command": "ls -la"}}
        assert run(base, home).returncode == 0
        assert run({**base, "tool_input": {"command": "DELETE FROM users WHERE id=1;"}}, home).returncode == 0

        blocked = [
            "rm -rf /tmp/demo",
            "DROP TABLE users;",
            "git push --force origin main",
            "TRUNCATE audit_log;",
            "DELETE FROM users;",
        ]
        for command in blocked:
            proc = run({**base, "tool_input": {"command": command}}, home)
            assert proc.returncode == 2, (command, proc.returncode, proc.stderr)
            assert "Blocked destructive bash command" in proc.stderr

        log = home / ".claude" / "hooks" / "blocked.log"
        lines = log.read_text().strip().splitlines()
        assert len(lines) == len(blocked), lines
        entries = [json.loads(line) for line in lines]
        assert entries[0]["attempted_command"] == "rm -rf /tmp/demo"
        assert entries[0]["project_path"] == "/repo"
    print("ok - destructive command hook tests passed")


if __name__ == "__main__":
    main()
