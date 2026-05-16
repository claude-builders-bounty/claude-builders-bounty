import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import block_destructive_bash as hook


class BlockDestructiveBashTest(unittest.TestCase):
    def assert_blocked(self, command: str, rule: str) -> None:
        decision = hook.classify_command(command)
        self.assertTrue(decision.blocked)
        self.assertEqual(decision.rule, rule)

    def assert_allowed(self, command: str) -> None:
        decision = hook.classify_command(command)
        self.assertFalse(decision.blocked)

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "rm-rf")
        self.assert_blocked("sudo rm -r -f ./tmp", "rm-rf")
        self.assert_blocked("env FOO=bar rm --recursive --force cache", "rm-rf")

    def test_allows_non_recursive_or_non_force_rm(self) -> None:
        self.assert_allowed("rm build/output.txt")
        self.assert_allowed("rm -r build")
        self.assert_allowed("rm -f build/output.txt")

    def test_blocks_force_pushes(self) -> None:
        self.assert_blocked("git push --force origin main", "git-force-push")
        self.assert_blocked("git push -f origin main", "git-force-push")
        self.assert_blocked("git push --force-with-lease origin main", "git-force-push")

    def test_allows_normal_git_pushes(self) -> None:
        self.assert_allowed("git push origin main")
        self.assert_allowed("git push --set-upstream origin feature")

    def test_blocks_dangerous_sql(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "drop-table")
        self.assert_blocked("mysql -e 'TRUNCATE TABLE events'", "truncate")
        self.assert_blocked("sqlite3 app.db 'DELETE FROM sessions'", "delete-without-where")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed("sqlite3 app.db 'DELETE FROM sessions WHERE expires_at < now()'")

    def test_log_blocked_attempt_writes_json_line(self) -> None:
        decision = hook.BlockDecision(True, "rm-rf", "rm with recursive and force flags is blocked")
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            hook.log_blocked_attempt("rm -rf build", "/repo", decision, log_path)
            record = json.loads(log_path.read_text(encoding="utf-8"))

        self.assertEqual(record["command"], "rm -rf build")
        self.assertEqual(record["project_path"], "/repo")
        self.assertEqual(record["rule"], "rm-rf")
        self.assertIn("timestamp", record)


if __name__ == "__main__":
    unittest.main()
