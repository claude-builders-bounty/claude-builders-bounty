"""Tests for block-destructive.py. Run: python -m unittest discover -s tests -v"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / "block-destructive.py"

spec = importlib.util.spec_from_file_location("block_destructive", HOOK)
guard = importlib.util.module_from_spec(spec)
sys.modules["block_destructive"] = guard  # dataclasses resolve the module via sys.modules
spec.loader.exec_module(guard)


BLOCKED = [
    # recursive force delete
    ("rm -rf /", "rm_rf"),
    ("rm -rf build/", "rm_rf"),
    ("rm -fr dist", "rm_rf"),
    ("rm -Rf ./node_modules", "rm_rf"),
    ("rm -r -f /tmp/work", "rm_rf"),
    ("rm --recursive --force /var/tmp/x", "rm_rf"),
    ("sudo rm -rf /usr/local/lib", "rm_rf"),
    ("sudo -u root rm -rf /srv", "rm_rf"),
    ("env -i PATH=/usr/bin rm -rf /home/user", "rm_rf"),
    ("nohup rm -rf logs &", "rm_rf"),
    ("xargs rm -rf < list.txt", "rm_rf"),
    ("echo cleaning && rm -rf ./out", "rm_rf"),
    ("cd /tmp; rm -rf /", "rm_rf"),
    ("bash -c 'rm -rf /'", "rm_rf"),
    ("sh -c \"sudo rm -rf /var/lib/data\"", "rm_rf"),
    ("eval 'rm -rf ~'", "rm_rf"),
    # git history rewrite
    ("git push --force", "git_push_force"),
    ("git push -f origin main", "git_push_force"),
    ("git push origin +main", "git_push_force"),
    ("git push --force-with-lease origin feature", "git_push_force"),
    ("sudo git push -f", "git_push_force"),
    # SQL
    ("psql -c 'DROP TABLE users'", "sql_drop_table"),
    ("psql -d app -c \"drop table if exists invoices;\"", "sql_drop_table"),
    ("sqlite3 app.db 'DROP TABLE sessions'", "sql_drop_table"),
    ("mysql -u root -e 'TRUNCATE TABLE logs'", "sql_truncate"),
    ("psql -c 'DELETE FROM users'", "sql_delete_without_where"),
    ("sqlite3 app.db 'delete from sessions;'", "sql_delete_without_where"),
    ("mysql -e 'DELETE FROM invoices'", "sql_delete_without_where"),
    ("psql -c 'DROP DATABASE production'", "sql_drop_database"),
]

ALLOWED = [
    # ordinary file operations
    "ls -la",
    "rm -f package-lock.json",
    "rm notes.md todo.md",
    "rm -r ./cache",
    "cp -r src dist",
    "mkdir -p build",
    # destructive-looking text in arguments is not an execution
    "echo 'rm -rf is dangerous'",
    "grep -rn 'DROP TABLE' migrations/",
    "git commit -m 'rm -rf cleanup and DROP TABLE notes'",
    "git log --grep 'push -f'",
    # git
    "git push origin main",
    "git push --set-upstream origin feature-x",
    "git status",
    "git commit -m 'feat: add invoices'",
    # SQL that is scoped or read-only
    "psql -c 'SELECT * FROM users'",
    "psql -c 'DELETE FROM users WHERE id = 1'",
    "psql -c 'delete from sessions where expires_at < now()'",
    "mysql -e 'UPDATE users SET active = 0 WHERE id = 3'",
    "sqlite3 app.db '.schema'",
    "npm run db:migrate",
    "npm test",
    # shell wrappers that are not destructive
    "bash -c 'npm run build'",
    "sh -c 'git status'",
]

EMPTY = ["", "   ", "\n"]


class EvaluationTests(unittest.TestCase):
    def test_blocks_destructive_commands(self):
        for command, expected_rule in BLOCKED:
            with self.subTest(command=command):
                decision = guard.evaluate(command)
                self.assertIsNotNone(decision, f"expected block: {command}")
                self.assertEqual(decision.rule, expected_rule)

    def test_allows_normal_commands(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(guard.evaluate(command), f"false positive: {command}")

    def test_empty_commands(self):
        for command in EMPTY:
            with self.subTest(command=repr(command)):
                self.assertIsNone(guard.evaluate(command))

    def test_reason_is_explained_to_claude(self):
        decision = guard.evaluate("rm -rf /")
        message = decision.message("rm -rf /")
        self.assertIn("BLOCKED", message)
        self.assertIn("Why:", message)
        self.assertIn("What to do instead:", message)
        self.assertIn("rm -rf /", message)
        self.assertIn(guard.ALLOW_ENV, message)

    def test_splitting_keeps_quoted_separators(self):
        segments = guard.split_segments("psql -c 'select 1; select 2' && ls")
        self.assertEqual(len(segments), 2)

    def test_depth_limit_terminates(self):
        nested = "bash -c " * 20 + "'ls'"
        self.assertIsNone(guard.evaluate(nested))


class HookProcessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "blocked.log"
        self.env = dict(os.environ, CLAUDE_HOOK_LOG=str(self.log))
        self.env.pop(guard.ALLOW_ENV, None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, command: str, env: dict | None = None):
        payload = {
            "session_id": "sess-1",
            "cwd": "/Users/dev/project",
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command, "description": "test"},
        }
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env or self.env,
            timeout=30,
        )

    def test_exit_code_two_and_reason_on_stderr(self):
        result = self.run_hook("rm -rf /")
        self.assertEqual(result.returncode, 2)
        self.assertIn("BLOCKED", result.stderr)
        self.assertIn("rm -rf", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_normal_command_passes_silently(self):
        result = self.run_hook("npm test")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.log.exists())

    def test_log_entry_has_required_fields(self):
        self.run_hook("git push --force origin main")
        self.assertTrue(self.log.exists())
        entry = json.loads(self.log.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["decision"], "blocked")
        self.assertEqual(entry["rule"], "git_push_force")
        self.assertEqual(entry["command"], "git push --force origin main")
        self.assertEqual(entry["project"], "/Users/dev/project")
        self.assertEqual(entry["session_id"], "sess-1")
        self.assertRegex(entry["timestamp"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")

    def test_bypass_env_allows_and_logs(self):
        env = dict(self.env, **{guard.ALLOW_ENV: "1"})
        result = self.run_hook("rm -rf /", env=env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("WARNING", result.stderr)
        entry = json.loads(self.log.read_text(encoding="utf-8").strip().splitlines()[-1])
        self.assertEqual(entry["decision"], "bypassed")

    def test_malformed_payload_fails_open(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            text=True,
            capture_output=True,
            env=self.env,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0)

    def test_missing_command_fails_open(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_name": "Read", "tool_input": {"file_path": "/etc/passwd"}}),
            text=True,
            capture_output=True,
            env=self.env,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0)

    def test_check_flag(self):
        blocked = subprocess.run(
            [sys.executable, str(HOOK), "--check", "rm -rf /"],
            text=True, capture_output=True, env=self.env, timeout=30,
        )
        allowed = subprocess.run(
            [sys.executable, str(HOOK), "--check", "ls"],
            text=True, capture_output=True, env=self.env, timeout=30,
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertEqual(allowed.returncode, 0)
        self.assertIn("allowed", allowed.stdout)


if __name__ == "__main__":
    unittest.main()
