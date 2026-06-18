"""Unit tests for pre-tool-use-block-destructive.py.

Run from the repo root:
    python -m unittest tests.test_pre_tool_use_block_destructive -v
"""
import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

# Load the hook module from ../hooks/pre-tool-use-block-destructive.py
HOOK_PATH = Path(__file__).resolve().parent.parent / "hooks" / "pre-tool-use-block-destructive.py"
_spec = importlib.util.spec_from_file_location("pre_tool_use_block_destructive", HOOK_PATH)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def make_payload(tool_name="Bash", command="", cwd="/tmp/project"):
    return {"tool_name": tool_name, "tool_input": {"command": command}, "cwd": cwd}


class TestCheckCommand(unittest.TestCase):
    def test_blocks_rm_rf_absolute(self):
        blocked, reason = hook.check_command("rm -rf /tmp/foo")
        self.assertTrue(blocked)
        self.assertIn("rm -rf", reason.lower())

    def test_blocks_rm_fr(self):
        blocked, _ = hook.check_command("rm -fr node_modules")
        self.assertTrue(blocked)

    def test_blocks_drop_table(self):
        blocked, reason = hook.check_command("DROP TABLE users;")
        self.assertTrue(blocked)
        self.assertIn("DROP", reason)

    def test_blocks_truncate(self):
        blocked, reason = hook.check_command("TRUNCATE TABLE logs")
        self.assertTrue(blocked)
        self.assertIn("TRUNCATE", reason)

    def test_blocks_truncate_without_table_keyword(self):
        blocked, _ = hook.check_command("TRUNCATE logs")
        self.assertTrue(blocked)

    def test_blocks_delete_from_without_where(self):
        blocked, reason = hook.check_command("DELETE FROM users;")
        self.assertTrue(blocked)
        self.assertIn("DELETE", reason)

    def test_allows_delete_from_with_where(self):
        blocked, _ = hook.check_command("DELETE FROM users WHERE id=5;")
        self.assertFalse(blocked)

    def test_blocks_git_push_force(self):
        blocked, reason = hook.check_command("git push --force origin main")
        self.assertTrue(blocked)
        self.assertIn("force", reason.lower())

    def test_blocks_git_push_f(self):
        blocked, _ = hook.check_command("git push -f origin main")
        self.assertTrue(blocked)

    def test_allows_normal_git_push(self):
        blocked, _ = hook.check_command("git push origin main")
        self.assertFalse(blocked)

    def test_allows_ls(self):
        blocked, _ = hook.check_command("ls -la")
        self.assertFalse(blocked)

    def test_allows_npm_install(self):
        blocked, _ = hook.check_command("npm install lodash")
        self.assertFalse(blocked)

    def test_allows_rm_single_file(self):
        blocked, _ = hook.check_command("rm foo.txt")
        self.assertFalse(blocked)

    def test_blocks_drop_database(self):
        blocked, _ = hook.check_command("DROP DATABASE production;")
        self.assertTrue(blocked)

    def test_blocks_drop_index(self):
        blocked, _ = hook.check_command("DROP INDEX idx_users_email;")
        self.assertTrue(blocked)


class TestMainAllowPath(unittest.TestCase):
    def run_main_with(self, payload: dict):
        with patch("sys.stdin", io.StringIO(json.dumps(payload))):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                rc = hook.main()
                return rc, out.getvalue()

    def test_non_bash_tools_allowed(self):
        payload = make_payload(tool_name="Read", command="")
        rc, output = self.run_main_with(payload)
        self.assertEqual(rc, 0)
        self.assertEqual(output, "")

    def test_normal_command_allowed(self):
        payload = make_payload(command="ls -la")
        rc, output = self.run_main_with(payload)
        self.assertEqual(rc, 0)
        self.assertEqual(output, "")

    def test_destructive_command_blocked(self):
        payload = make_payload(command="rm -rf /tmp/foo")
        rc, output = self.run_main_with(payload)
        self.assertEqual(rc, 0)
        decision = json.loads(output)
        self.assertEqual(decision["decision"], "block")
        self.assertIn("Blocked by", decision["reason"])

    def test_invalid_json_returns_allow(self):
        with patch("sys.stdin", io.StringIO("not json{")):
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                rc = hook.main()
                self.assertEqual(rc, 0)
                self.assertEqual(out.getvalue(), "")


class TestLogBlockFile(unittest.TestCase):
    def test_log_appends(self, tmp_path=None):
        # Use a tmp log file
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
            tmp_log = f.name
        try:
            with patch.object(hook, "LOG_PATH", Path(tmp_log)):
                hook.log_blocked("rm -rf /", "test reason", "/test/project")
                content = Path(tmp_log).read_text(encoding="utf-8")
                self.assertIn("BLOCKED: test reason", content)
                self.assertIn("rm -rf /", content)
                self.assertIn("/test/project", content)
                self.assertIn("[", content)  # timestamp starts with [
        finally:
            Path(tmp_log).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
