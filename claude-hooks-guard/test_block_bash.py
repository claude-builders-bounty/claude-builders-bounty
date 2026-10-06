#!/usr/bin/env python3
"""Tests for block_bash.py. Run: python3 test_block_bash.py"""
import importlib.util
import json
import os
import sys
import unittest

spec = importlib.util.spec_from_file_location("block_bash", os.path.join(os.path.dirname(__file__), "block_bash.py"))
bb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bb)

BLOCKED = [
    "rm -rf /",
    "rm -rf ~",
    "rm -fr node_modules",
    "sudo rm -rf /var/data",
    "rm -r --force ./build",
    "DROP TABLE users;",
    "drop   table  if exists orders;",
    "DROP TEMPORARY TABLE sessions;",
    "git push --force",
    "git push origin main --force",
    "git push -f origin feature",
    "git push origin main +main:refs/heads/main",
    "TRUNCATE TABLE audit_log;",
    "DELETE FROM users;",
    "delete from orders",
    "echo hi && rm -rf /",
    "ls; DROP TABLE accounts",
    "grep -r 'DROP TABLE' . ; rm -rf /tmp/x",
]

ALLOWED = [
    "ls -la",
    "rm file.txt",
    "rm -r build/",
    "git push origin feature/bump",
    "git status",
    "npm test",
    "python3 manage.py migrate",
    "echo 'run rm -rf build to clean'",
    "grep -rn 'rm -rf' ./docs",
    "sed -i 's/foo/bar/' file.txt",
    "cat package.json",
    "mkdir -p out && echo ok",
    "git commit -m 'fix: handle empty input'",
    "kubectl delete pod api-1",
]


class TestLogPath(unittest.TestCase):
    def test_default_log_path_is_inside_the_hooks_dir(self):
        self.assertTrue(
            bb.LOG_PATH.endswith(os.path.join(".claude", "hooks", "blocked.log")),
            bb.LOG_PATH,
        )


class TestBlocking(unittest.TestCase):
    def test_dangerous_commands_are_caught(self):
        for cmd in BLOCKED:
            with self.subTest(cmd=cmd):
                self.assertTrue(bb.find_violations(cmd), f"expected block: {cmd}")

    def test_normal_commands_pass(self):
        for cmd in ALLOWED:
            with self.subTest(cmd=cmd):
                self.assertEqual(bb.find_violations(cmd), [], f"false positive: {cmd}")

    def test_where_clause_delete_is_allowed(self):
        self.assertEqual(bb.find_violations("DELETE FROM users WHERE id = 42"), [])

    def test_quoting_cannot_hide_the_command(self):
        self.assertTrue(bb.find_violations("bash -c 'rm -rf /'"))
        self.assertTrue(bb.find_violations('rm -rf "$HOME"'))
        self.assertTrue(bb.find_violations("x=1; rm -fr ${TARGET}"))

    def test_main_denies_and_logs(self):
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            bb.LOG_PATH = os.path.join(home, ".claude", "hooks", "blocked.log")
            payload = json.dumps(
                {
                    "cwd": "/tmp/project",
                    "tool_input": {"command": "rm -rf /"},
                }
            )
            stdin, sys.stdin = sys.stdin, io.StringIO(payload)
            stdout, sys.stdout = sys.stdout, io.StringIO()
            try:
                code = bb.main()
                emitted = sys.stdout.getvalue()
            finally:
                sys.stdin, sys.stdout = stdin, stdout

            self.assertEqual(code, 0)
            out = json.loads(emitted)
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("BLOCKED", out["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertTrue(os.path.exists(bb.LOG_PATH))
            with open(bb.LOG_PATH, encoding="utf-8") as fh:
                log = fh.read()
            self.assertIn("project=/tmp/project", log)
            self.assertIn("rm -rf /", log)

    def test_main_allows_silently(self):
        import io
        import tempfile

        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            bb.LOG_PATH = os.path.join(home, ".claude", "hooks", "blocked.log")
            payload = json.dumps({"cwd": "/tmp/p", "tool_input": {"command": "ls -la"}})
            stdin, sys.stdin = sys.stdin, io.StringIO(payload)
            stdout, sys.stdout = sys.stdout, io.StringIO()
            try:
                bb.main()
                emitted = sys.stdout.getvalue()
            finally:
                sys.stdin, sys.stdout = stdin, stdout
            self.assertEqual(emitted, "")
            self.assertFalse(os.path.exists(bb.LOG_PATH))


if __name__ == "__main__":
    unittest.main(verbosity=2)
