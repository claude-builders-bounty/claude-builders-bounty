import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK_SCRIPT = Path(__file__).resolve().parent.parent / "hooks" / "block-destructive-bash.py"


class TestBlockDestructiveBashHook(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = Path(self.temp_dir.name) / "blocked.log"
        self.env = os.environ.copy()
        self.env["CLAUDE_HOOK_LOG_FILE"] = str(self.log_file)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_hook(self, command: str, tool_name: str = "Bash", cwd: str = "/workspace/demo-app") -> subprocess.CompletedProcess:
        payload = {
            "session_id": "test-session-123",
            "cwd": cwd,
            "hook_event_name": "PreToolUse",
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
        return subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
        )

    def test_blocks_rm_rf_variants(self) -> None:
        for cmd in [
            "rm -rf /tmp/build",
            "sudo rm -fr ./dist",
            "rm -r -f node_modules",
            "rm --recursive --force /var/tmp/cache",
            "echo start && rm -Rf build/",
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 2, f"Expected {cmd!r} to be blocked")
                self.assertIn("BLOCKED BY CLAUDE CODE HOOK", res.stderr)
                self.assertIn("rm", res.stderr)

    def test_blocks_drop_table_and_database(self) -> None:
        for cmd in [
            'psql -c "DROP TABLE users;"',
            "sqlite3 app.db 'drop table if exists sessions'",
            'mysql -e "DROP DATABASE production;"',
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 2, f"Expected {cmd!r} to be blocked")
                self.assertIn("DROP", res.stderr)

    def test_blocks_git_push_force(self) -> None:
        for cmd in [
            "git push --force origin main",
            "git push -f origin feat/branch",
            "git status && git push --force",
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 2, f"Expected {cmd!r} to be blocked")
                self.assertIn("git push", res.stderr)

    def test_blocks_truncate(self) -> None:
        for cmd in [
            'psql -c "TRUNCATE TABLE audit_logs;"',
            'psql -c "TRUNCATE users RESTART IDENTITY CASCADE;"',
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 2, f"Expected {cmd!r} to be blocked")
                self.assertIn("TRUNCATE", res.stderr)

    def test_blocks_delete_from_without_where(self) -> None:
        for cmd in [
            'sqlite3 data.db "DELETE FROM accounts;"',
            'psql -c "DELETE FROM orders"',
            'psql -c "SELECT 1; DELETE FROM sessions;"',
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 2, f"Expected {cmd!r} to be blocked")
                self.assertIn("DELETE FROM", res.stderr)

    def test_allows_delete_from_with_where_and_normal_commands(self) -> None:
        for cmd in [
            'sqlite3 data.db "DELETE FROM accounts WHERE id = 42;"',
            'psql -c "DELETE FROM sessions WHERE expired_at < NOW();"',
            "ls -la",
            "git status",
            "git push origin main",
            "rm temp.txt",
            "rm -r empty_dir",
            "npm test",
            "pytest -q",
        ]:
            with self.subTest(cmd=cmd):
                res = self.run_hook(cmd)
                self.assertEqual(res.returncode, 0, f"Expected {cmd!r} to be allowed, stderr={res.stderr}")
                self.assertEqual(res.stderr, "")

    def test_logs_blocked_attempts_with_timestamp_command_and_project_path(self) -> None:
        res = self.run_hook("rm -rf /important/data", cwd="/home/dev/my-saas-project")
        self.assertEqual(res.returncode, 2)
        self.assertTrue(self.log_file.exists())
        content = self.log_file.read_text(encoding="utf-8")
        self.assertIn("project=/home/dev/my-saas-project", content)
        self.assertIn("command=rm -rf /important/data", content)
        self.assertRegex(content, r"\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\]")


if __name__ == "__main__":
    unittest.main()
