import unittest
import tempfile
import os
import shutil
from guard_hook import evaluate_command, log_blocked

class TestGuardHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_blocks_rm_rf(self):
        allowed, _ = evaluate_command("rm -rf /var/data")
        self.assertFalse(allowed)
        allowed, _ = evaluate_command("rm -fr /home/user")
        self.assertFalse(allowed)

    def test_blocks_git_force_push(self):
        allowed, _ = evaluate_command("git push origin main --force")
        self.assertFalse(allowed)
        allowed, _ = evaluate_command("git push -f origin main")
        self.assertFalse(allowed)

    def test_blocks_drop_table(self):
        allowed, _ = evaluate_command("psql -c 'DROP TABLE users;'")
        self.assertFalse(allowed)

    def test_blocks_truncate(self):
        allowed, _ = evaluate_command("mysql -e 'TRUNCATE accounts;'")
        self.assertFalse(allowed)

    def test_blocks_delete_without_where(self):
        allowed, _ = evaluate_command("sqlite3 db.sqlite 'DELETE FROM users;'")
        self.assertFalse(allowed)

    def test_allows_delete_with_where(self):
        allowed, _ = evaluate_command("sqlite3 db.sqlite 'DELETE FROM users WHERE id = 12;'")
        self.assertTrue(allowed)

    def test_allows_safe_commands(self):
        safe_cmds = [
            "ls -la",
            "git status",
            "git push origin main",
            "python app.py",
            "npm test",
            "rm safe_file.txt"
        ]
        for cmd in safe_cmds:
            allowed, _ = evaluate_command(cmd)
            self.assertTrue(allowed, f"Failed on safe command: {cmd}")

    def test_logging(self):
        log_blocked("rm -rf /test", "Testing block", log_dir=self.temp_dir)
        log_file = os.path.join(self.temp_dir, "blocked.log")
        self.assertTrue(os.path.exists(log_file))
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("rm -rf /test", content)
            self.assertIn("Testing block", content)

if __name__ == "__main__":
    unittest.main()
