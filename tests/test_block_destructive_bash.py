import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from hooks import block_destructive_bash as hook


class BlockDestructiveBashTests(unittest.TestCase):
    def run_hook(self, command, *, tool_name="Bash", cwd="/repo"):
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": cwd,
        }
        stdin = io.StringIO(json.dumps(payload))
        stderr = io.StringIO()
        with tempfile.TemporaryDirectory() as home:
            with patch("sys.stdin", stdin), patch.dict(os.environ, {"HOME": home}):
                with redirect_stderr(stderr):
                    code = hook.main()
                log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
                log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        return code, stderr.getvalue(), log

    def assert_blocked(self, command, expected_reason):
        code, stderr, log = self.run_hook(command)
        self.assertEqual(code, 2)
        self.assertIn(expected_reason, stderr)
        entry = json.loads(log)
        self.assertEqual(entry["command"], command)
        self.assertEqual(entry["project_path"], "/repo")
        self.assertIn(expected_reason, entry["reason"])
        self.assertIn("timestamp", entry)

    def assert_allowed(self, command):
        code, stderr, log = self.run_hook(command)
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(log, "")

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf ./dist", "rm with both recursive and force")

    def test_blocks_rm_fr(self):
        self.assert_blocked("rm -fr ./dist", "rm with both recursive and force")

    def test_blocks_sudo_rm_rf(self):
        self.assert_blocked("sudo rm -rf /tmp/build", "rm with both recursive and force")

    def test_blocks_drop_table(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")

    def test_blocks_truncate(self):
        self.assert_blocked("mysql -e 'TRUNCATE TABLE users'", "TRUNCATE")

    def test_blocks_delete_from_without_where(self):
        self.assert_blocked("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM without WHERE")

    def test_blocks_git_push_force_long(self):
        self.assert_blocked("git push --force origin main", "git push with force")

    def test_blocks_git_push_force_short(self):
        self.assert_blocked("git push -f origin main", "git push with force")

    def test_blocks_git_push_force_with_lease(self):
        self.assert_blocked("git push --force-with-lease origin main", "git push with force")

    def test_blocks_nested_bash_rm_rf(self):
        self.assert_blocked('bash -c "rm -rf ./dist"', "rm with both recursive and force")

    def test_allows_echoed_rm_rf(self):
        self.assert_allowed('echo "rm -rf /"')

    def test_allows_grep_drop_table(self):
        self.assert_allowed('grep "DROP TABLE" file.sql')

    def test_allows_delete_with_where(self):
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1'")

    def test_allows_normal_git_push(self):
        self.assert_allowed("git push origin main")

    def test_allows_rm_recursive_without_force(self):
        self.assert_allowed("rm -r ./tmp")

    def test_allows_rm_force_without_recursive(self):
        self.assert_allowed("rm -f ./file.txt")

    def test_allows_non_sql_executor_with_sql_text(self):
        self.assert_allowed('python3 -c "print(\\"DROP TABLE users\\")"')

    def test_allows_nested_bash_echoed_rm_rf(self):
        self.assert_allowed('bash -c "echo rm -rf /"')

    def test_ignores_non_bash_tools(self):
        code, stderr, log = self.run_hook("rm -rf ./dist", tool_name="Read")
        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
