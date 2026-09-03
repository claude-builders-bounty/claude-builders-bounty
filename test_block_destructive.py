#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HOOK = os.path.join(HERE, "block_destructive.py")


def run(command, cwd="/tmp/demo"):
    payload = json.dumps({
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    })
    env = os.environ.copy()
    env["HOME"] = tempfile.mkdtemp()
    proc = subprocess.run(
        [sys.executable, HOOK],
        input=payload.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    out = proc.stdout.decode().strip()
    data = json.loads(out) if out else None
    return proc.returncode, data, env["HOME"]


class HookTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        code, data, home = run("rm -rf /tmp/build")
        self.assertEqual(code, 0)
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
        log = open(os.path.join(home, ".claude", "hooks", "blocked.log")).read()
        self.assertIn("rm -rf /tmp/build", log)

    def test_blocks_force_push(self):
        _, data, _ = run("git push origin main --force")
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_drop_table(self):
        _, data, _ = run("psql -c 'DROP TABLE users'")
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_truncate(self):
        _, data, _ = run("mysql -e 'TRUNCATE invoices'")
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_blocks_delete_without_where(self):
        _, data, _ = run("mysql -e 'DELETE FROM users'")
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_allows_delete_with_where(self):
        code, data, _ = run("mysql -e 'DELETE FROM users WHERE id=1'")
        self.assertEqual(code, 0)
        self.assertIsNone(data)

    def test_allows_normal_bash(self):
        code, data, _ = run("ls -la && git status")
        self.assertEqual(code, 0)
        self.assertIsNone(data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
