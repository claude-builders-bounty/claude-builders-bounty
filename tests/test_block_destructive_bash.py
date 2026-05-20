import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "hooks"
    / "block-destructive-bash"
    / "block_destructive_bash.py"
)

spec = importlib.util.spec_from_file_location("block_destructive_bash", MODULE_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def payload(command):
    return {
        "session_id": "test-session",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/repo/project",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


class BlockDestructiveBashTest(unittest.TestCase):
    def run_hook(self, command):
        with tempfile.TemporaryDirectory() as home:
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout):
                    exit_code = hook.handle_hook(payload(command))
                log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
                log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home

        return exit_code, stdout.getvalue(), log_text

    def assert_blocked(self, command, reason_fragment):
        exit_code, stdout, log_text = self.run_hook(command)
        self.assertEqual(exit_code, 0)
        response = json.loads(stdout)
        decision = response["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(reason_fragment, decision["permissionDecisionReason"])
        log_entry = json.loads(log_text)
        self.assertEqual(log_entry["command"], command)
        self.assertEqual(log_entry["project_path"], "/repo/project")
        self.assertIn(reason_fragment, log_entry["reason"])

    def test_blocks_rm_rf(self):
        self.assert_blocked("sudo rm -rf dist", "rm with recursive and force")

    def test_blocks_drop_table(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")

    def test_blocks_git_push_force(self):
        self.assert_blocked("git push --force origin main", "git push with force")

    def test_blocks_truncate(self):
        self.assert_blocked('psql -c "TRUNCATE TABLE audit_log"', "TRUNCATE")

    def test_blocks_delete_without_where(self):
        self.assert_blocked('psql -c "DELETE FROM sessions"', "DELETE FROM without a WHERE")

    def test_allows_delete_with_where(self):
        exit_code, stdout, log_text = self.run_hook('psql -c "DELETE FROM sessions WHERE id = 1"')
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_allows_normal_bash(self):
        exit_code, stdout, log_text = self.run_hook("npm test")
        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(log_text, "")

    def test_ignores_non_bash_tools(self):
        event = payload("rm -rf dist")
        event["tool_name"] = "Read"
        with tempfile.TemporaryDirectory() as home:
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            try:
                self.assertEqual(hook.handle_hook(event), 0)
                self.assertFalse((Path(home) / ".claude" / "hooks" / "blocked.log").exists())
            finally:
                if old_home is None:
                    os.environ.pop("HOME", None)
                else:
                    os.environ["HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
