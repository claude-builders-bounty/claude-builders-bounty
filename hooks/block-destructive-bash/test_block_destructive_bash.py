import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).with_name("block_destructive_bash.py")
spec = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
blocker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocker)


class DestructiveBashBlockerTests(unittest.TestCase):
    def assert_blocked(self, command, label):
        reason = blocker.destructive_reason(command)
        self.assertIsNotNone(reason)
        self.assertIn(label, reason)

    def assert_allowed(self, command):
        self.assertIsNone(blocker.destructive_reason(command))

    def test_blocks_rm_rf(self):
        self.assert_blocked("rm -rf dist", "rm -rf")
        self.assert_blocked("rm -fr ./tmp", "rm -rf")
        self.assert_blocked("echo ok && rm -rf /tmp/build", "rm -rf")

    def test_blocks_force_push(self):
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push --force-with-lease origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")

    def test_blocks_sql_destructive_patterns(self):
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE TABLE audit_log'", "TRUNCATE")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM sessions'", "DELETE FROM without WHERE")

    def test_allows_normal_commands(self):
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm -r tmp")
        self.assert_allowed("truncate -s 0 app.log")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE id = 1'")
        self.assert_allowed("npm test")


if __name__ == "__main__":
    unittest.main()
