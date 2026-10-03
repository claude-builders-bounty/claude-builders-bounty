import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "destructive_guard.py"

spec = importlib.util.spec_from_file_location("destructive_guard", GUARD)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


class PatternTests(unittest.TestCase):
    def test_blocks_rm_rf(self):
        self.assertIsNotNone(guard.destructive_reason("rm -rf /tmp/demo"))

    def test_blocks_rm_fr(self):
        self.assertIsNotNone(guard.destructive_reason("rm -fr build"))

    def test_blocks_drop_table_case_insensitive(self):
        self.assertIsNotNone(guard.destructive_reason("psql -c 'DrOp TaBlE users'"))

    def test_blocks_force_push(self):
        self.assertIsNotNone(guard.destructive_reason("git push origin main --force"))

    def test_blocks_force_with_lease(self):
        self.assertIsNotNone(guard.destructive_reason("git push --force-with-lease origin main"))

    def test_blocks_truncate(self):
        self.assertIsNotNone(guard.destructive_reason("mysql -e 'TRUNCATE TABLE audit_log'"))

    def test_blocks_delete_without_where(self):
        self.assertIsNotNone(guard.destructive_reason("psql -c 'DELETE FROM sessions'"))

    def test_allows_delete_with_where(self):
        self.assertIsNone(guard.destructive_reason("psql -c 'DELETE FROM sessions WHERE expired = true'"))

    def test_allows_normal_git_push(self):
        self.assertIsNone(guard.destructive_reason("git push origin feature/safe"))

    def test_allows_normal_rm(self):
        self.assertIsNone(guard.destructive_reason("rm build.log"))


class HookContractTests(unittest.TestCase):
    def run_hook(self, command: str):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env["HOME"] = temp
            payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": "/work/project"}
            completed = subprocess.run(
                [sys.executable, str(GUARD)],
                input=json.dumps(payload),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
            log = Path(temp) / ".claude" / "hooks" / "blocked.log"
            return completed, log.read_text(encoding="utf-8") if log.exists() else ""

    def test_blocked_command_exits_two_and_logs_fields(self):
        completed, log = self.run_hook("DELETE FROM users")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("Blocked destructive Bash command", completed.stderr)
        row = json.loads(log.strip())
        self.assertEqual(row["attempted_command"], "DELETE FROM users")
        self.assertEqual(row["project_path"], "/work/project")
        self.assertIn("timestamp", row)

    def test_safe_command_exits_zero_without_log(self):
        completed, log = self.run_hook("echo hello")
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(log, "")


if __name__ == "__main__":
    unittest.main()
