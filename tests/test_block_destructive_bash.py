#!/usr/bin/env python3
"""Tests for block_destructive_bash.py — run: python3 -m pytest tests/ -q
or plain: python3 tests/test_block_destructive_bash.py
"""
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

HOOK = os.path.join(
    os.path.dirname(__file__), "..", "hooks", "pre-tool-use",
    "block_destructive_bash.py",
)
spec = importlib.util.spec_from_file_location("hook", HOOK)
hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hook)


def run_hook(command, tool="Bash"):
    event = {"tool_name": tool, "tool_input": {"command": command},
             "cwd": "/tmp/proj"}
    out = io.StringIO()
    with mock.patch.object(sys, "stdin", io.StringIO(json.dumps(event))), \
         mock.patch.object(hook, "LOG_PATH",
                           os.path.join(tempfile.mkdtemp(), "blocked.log")), \
         redirect_stdout(out):
        rc = hook.main()
    return rc, out.getvalue()


class TestBlocked(unittest.TestCase):
    def assertBlocked(self, cmd):
        _, out = run_hook(cmd)
        self.assertIn('"deny"', out, f"should block: {cmd}")

    def test_rm_rf(self):
        self.assertBlocked("rm -rf /tmp/x")
        self.assertBlocked("rm -fr build")
        self.assertBlocked("cd /tmp && rm -Rf .")
        self.assertBlocked("ls; rm -r -f node_modules")

    def test_drop_table(self):
        self.assertBlocked('psql -c "DROP TABLE users;"')
        self.assertBlocked("mysql -e 'drop table sessions'")

    def test_git_force_push(self):
        self.assertBlocked("git push --force origin main")
        self.assertBlocked("git push -f")
        self.assertBlocked("git push origin main --force")

    def test_truncate(self):
        self.assertBlocked('psql -c "TRUNCATE TABLE events;"')
        self.assertBlocked("sqlite3 app.db 'TRUNCATE logs'")

    def test_delete_without_where(self):
        self.assertBlocked('psql -c "DELETE FROM users;"')
        self.assertBlocked("mysql -e 'delete from sessions'")


class TestAllowed(unittest.TestCase):
    def assertAllowed(self, cmd):
        _, out = run_hook(cmd)
        self.assertEqual(out.strip(), "", f"should allow: {cmd}")

    def test_normal_commands(self):
        self.assertAllowed("ls -la")
        self.assertAllowed("rm file.txt")
        self.assertAllowed("rm -r empty_dir")
        self.assertAllowed("git push origin main")
        self.assertAllowed("git push --force-with-lease origin main")
        self.assertAllowed("npm test && git status")

    def test_delete_with_where(self):
        self.assertAllowed('psql -c "DELETE FROM users WHERE id = 1;"')

    def test_non_bash_tool(self):
        _, out = run_hook("rm -rf /", tool="Read")
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
