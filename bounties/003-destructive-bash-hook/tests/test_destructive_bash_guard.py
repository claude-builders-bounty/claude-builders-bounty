from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


HOOK_PATH = Path(__file__).resolve().parents[1] / "destructive_bash_guard.py"
SPEC = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(guard)


class DestructiveBashGuardTest(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        self.assertIsNone(guard.find_block_reason("npm test"))

    def test_blocks_rm_rf_variants(self) -> None:
        cases = [
            "rm -rf /tmp/build",
            "sudo rm -r -f ./dist",
            "sudo -u root rm -rf ./dist",
            "sudo --user=root rm -rf ./dist",
            "/bin/rm -rf ./dist",
            "rm --recursive --force old-cache",
            "env CI=1 rm -fr node_modules",
            "env -u DEBUG CI=1 rm -rf node_modules",
            "command rm -rf cache",
            "npm test && rm -rf coverage",
            "printf done | rm -rf scratch",
            "echo ok\nrm -rf build",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIn("recursive remove", guard.find_block_reason(command))

    def test_does_not_treat_rm_text_or_non_recursive_delete_as_execution(self) -> None:
        cases = [
            'echo "rm -rf /"',
            'printf "rm -rf ./build"',
            'grep "rm -rf" README.md',
            'python -c "print(\'rm -rf /\')"',
            "rm -df empty-dir",
            "rm -f file.txt",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_respects_double_dash_for_rm_filenames(self) -> None:
        self.assertIsNone(guard.find_block_reason("rm -- -rf"))

    def test_blocks_force_push_variants(self) -> None:
        cases = [
            "git push --force origin main",
            "git push -f origin main",
            "/usr/bin/git push --force origin main",
            "sudo git push --force-with-lease origin main",
            "sudo -u deploy git push --force origin main",
            "env CI=1 git push -f origin main",
            "git -C /tmp/repo push --force origin main",
            "git -c core.hooksPath=/dev/null push --force origin main",
            "git --git-dir=/tmp/repo/.git push --force origin main",
            "git push origin +main:main",
            "git status && git push --force origin main",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIn("force-push", guard.find_block_reason(command))

    def test_does_not_treat_force_push_text_as_execution(self) -> None:
        cases = [
            'echo "git push --force origin main"',
            'printf "git push -f"',
            'grep "git push --force" README.md',
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_blocks_drop_truncate_and_delete_without_where(self) -> None:
        cases = {
            'psql -c "DROP TABLE users"': "DROP TABLE",
            "mysql -e 'TRUNCATE sessions'": "TRUNCATE",
            'psql -c "DELETE FROM users"': "DELETE FROM",
            'echo "DROP TABLE users" | psql': "DROP TABLE",
            'printf "TRUNCATE sessions" | sqlite3 app.db': "TRUNCATE",
            "DELETE FROM users": "DELETE FROM",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertIn(expected, guard.find_block_reason(command))

    def test_blocks_unbounded_delete_even_if_later_statement_has_where(self) -> None:
        command = 'psql -c "DELETE FROM audit_log; DELETE FROM users WHERE id = 1"'
        self.assertIn("DELETE FROM", guard.find_block_reason(command))

    def test_allows_delete_with_where(self) -> None:
        cases = [
            'psql -c "DELETE FROM users WHERE id = 1"',
            "DELETE FROM users WHERE inactive = true",
            'echo "DELETE FROM users WHERE id = 1" | psql',
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_allows_text_only_sql_mentions(self) -> None:
        cases = [
            'echo "DROP TABLE users"',
            'grep "DELETE FROM" migrations/*.sql',
            'printf "TRUNCATE sessions"',
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assertIsNone(guard.find_block_reason(command))

    def test_denies_and_logs_blocked_pre_tool_use(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            guard.BLOCKED_LOG = Path(tmpdir) / "blocked.log"
            payload = {
                "cwd": "/workspace/demo",
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
            }

            stdin = io.StringIO(json.dumps(payload))
            stdout = io.StringIO()
            with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
                self.assertEqual(guard.main(), 0)

            output = json.loads(stdout.getvalue())
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("recursive remove", hook_output["permissionDecisionReason"])

            log_entry = json.loads(guard.BLOCKED_LOG.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["project_path"], "/workspace/demo")
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertIn("timestamp", log_entry)
            self.assertIn("reason", log_entry)

    def test_appends_multiple_blocked_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            guard.BLOCKED_LOG = Path(tmpdir) / "blocked.log"
            for command in ("rm -rf build", "git push --force origin main"):
                guard.log_block({"cwd": "/workspace/demo"}, command, "blocked")

            entries = [
                json.loads(line)
                for line in guard.BLOCKED_LOG.read_text(encoding="utf-8").splitlines()
            ]
            self.assertEqual(
                [entry["command"] for entry in entries],
                ["rm -rf build", "git push --force origin main"],
            )

    def test_ignores_non_bash_tools(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "/tmp/example"},
        }

        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
            self.assertEqual(guard.main(), 0)

        self.assertEqual(stdout.getvalue(), "")

    def test_malformed_or_non_object_json_fails_open(self) -> None:
        for raw in ("not-json", "[]", "null"):
            with self.subTest(raw=raw):
                stdin = io.StringIO(raw)
                stdout = io.StringIO()
                with mock.patch("sys.stdin", stdin), redirect_stdout(stdout):
                    self.assertEqual(guard.main(), 0)
                self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
