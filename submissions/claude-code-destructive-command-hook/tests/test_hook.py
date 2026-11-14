#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Claude Code destructive-command hook."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "block_dangerous_bash.py"


def run_hook(payload, log_path):
    env = dict(os.environ)
    env["CLAUDE_HOOK_LOG"] = str(log_path)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    return proc


class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hook-test-", dir=str(ROOT)))
        self.log = self.tmp / "blocked.log"

    def tearDown(self):
        for p in sorted(self.tmp.rglob("*"), reverse=True):
            try:
                p.unlink() if p.is_file() else p.rmdir()
            except OSError:
                pass
        self.tmp.rmdir()

    def bash(self, command):
        return {"tool_name": "Bash", "tool_input": {"command": command, "cwd": str(self.tmp)}}

    def test_blocks_rm_rf(self):
        proc = run_hook(self.bash("rm -rf /tmp/build"), self.log)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("Blocked", proc.stderr)
        self.assertIn("rm -rf", self.log.read_text(encoding="utf-8"))

    def test_blocks_drop_table(self):
        proc = run_hook(self.bash("psql -c 'DROP TABLE users'"), self.log)
        self.assertEqual(proc.returncode, 2)

    def test_blocks_force_push(self):
        proc = run_hook(self.bash("git push --force origin main"), self.log)
        self.assertEqual(proc.returncode, 2)

    def test_blocks_truncate(self):
        proc = run_hook(self.bash("mysql -e 'TRUNCATE logs'"), self.log)
        self.assertEqual(proc.returncode, 2)

    def test_blocks_delete_without_where(self):
        proc = run_hook(self.bash("echo 'DELETE FROM users' | psql"), self.log)
        self.assertEqual(proc.returncode, 2)

    def test_allows_delete_with_where(self):
        proc = run_hook(self.bash("psql -c 'DELETE FROM users WHERE id = 1'"), self.log)
        self.assertEqual(proc.returncode, 0)

    def test_allows_normal_commands(self):
        for cmd in ["ls -la", "git status", "python3 app.py", "rm -f file.txt"]:
            with self.subTest(cmd=cmd):
                proc = run_hook(self.bash(cmd), self.log)
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_non_bash_tool_allowed(self):
        proc = run_hook({"tool_name": "Read", "tool_input": {"file_path": "/tmp/x"}}, self.log)
        self.assertEqual(proc.returncode, 0)

    def test_malformed_input_allowed(self):
        proc = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0)

    def test_log_has_fields(self):
        run_hook(self.bash("rm -rf /tmp/x"), self.log)
        line = json.loads(self.log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(line["pattern"], "rm -rf")
        self.assertEqual(line["command"], "rm -rf /tmp/x")
        self.assertIn("timestamp", line)
        self.assertIn("cwd", line)


if __name__ == "__main__":
    unittest.main()
