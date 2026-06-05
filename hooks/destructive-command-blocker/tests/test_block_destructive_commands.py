import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


HOOK_PATH = Path(__file__).resolve().parents[1] / "block_destructive_commands.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_commands", HOOK_PATH)
hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hook)


class DestructiveCommandBlockerTest(unittest.TestCase):
    def test_blocks_rm_rf_variants(self):
        self.assertEqual(hook.find_block_reason("rm -rf build"), "rm -rf")
        self.assertEqual(hook.find_block_reason("sudo /bin/rm -fr /tmp/example"), "rm -rf")

    def test_blocks_destructive_sql(self):
        self.assertEqual(hook.find_block_reason('psql -c "DROP TABLE users"'), "DROP TABLE")
        self.assertEqual(hook.find_block_reason('sqlite3 app.db "TRUNCATE TABLE sessions"'), "TRUNCATE")
        self.assertEqual(
            hook.find_block_reason('sqlite3 app.db "DELETE FROM sessions"'),
            "DELETE FROM without WHERE",
        )

    def test_allows_delete_with_where(self):
        self.assertIsNone(
            hook.find_block_reason('sqlite3 app.db "DELETE FROM sessions WHERE id = 1"')
        )

    def test_blocks_force_push(self):
        self.assertEqual(hook.find_block_reason("git push --force origin main"), "git push --force")
        self.assertEqual(hook.find_block_reason("git push -f origin main"), "git push --force")
        self.assertEqual(
            hook.find_block_reason("git push --force-with-lease=main origin main"),
            "git push --force",
        )

    def test_allows_normal_commands(self):
        self.assertIsNone(hook.find_block_reason("python -m pytest"))
        self.assertIsNone(hook.find_block_reason("git push origin main"))
        self.assertIsNone(hook.find_block_reason("rm -r build"))

    def test_main_exits_two_and_logs_blocked_bash_command(self):
        payload = {
            "tool_name": "Bash",
            "cwd": "/example/project",
            "tool_input": {"command": "rm -rf build"},
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "blocked.log"
            stdin = io.StringIO(json.dumps(payload))
            stderr = io.StringIO()
            with patch.object(sys, "stdin", stdin), patch.object(sys, "stderr", stderr):
                with patch.dict(os.environ, {"CLAUDE_BLOCKER_LOG": str(log_file)}):
                    self.assertEqual(hook.main(), 2)

            log_entry = json.loads(log_file.read_text(encoding="utf-8"))
            self.assertEqual(log_entry["project_path"], "/example/project")
            self.assertEqual(log_entry["command"], "rm -rf build")
            self.assertEqual(log_entry["reason"], "rm -rf")
            self.assertIn("Blocked destructive Bash command", stderr.getvalue())

    def test_main_allows_non_bash_tools(self):
        payload = {"tool_name": "Read", "tool_input": {"command": "rm -rf build"}}

        stdin = io.StringIO(json.dumps(payload))
        with patch.object(sys, "stdin", stdin):
            self.assertEqual(hook.main(), 0)


if __name__ == "__main__":
    unittest.main()
