import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


class DestructiveBashHookTests(unittest.TestCase):
    def test_detects_required_destructive_patterns(self):
        cases = [
            ("rm -rf ./dist", "rm -rf"),
            ("rm -fr ./dist", "rm -rf"),
            ("rm -r -f ./dist", "rm -rf"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push origin main --force", "git push --force"),
            ("git push -f origin main", "git push --force"),
            ("git push --force-with-lease", "git push --force"),
            ("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE"),
            ("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM"),
        ]

        for command, expected in cases:
            with self.subTest(command=command):
                reasons = hook.detect_block_reasons(command)
                self.assertTrue(any(expected in reason for reason in reasons))

    def test_allows_normal_bash_commands(self):
        cases = [
            "npm test",
            "git push origin feature/safe-branch",
            "rm -r ./dist",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
            "psql -c 'SELECT * FROM users'",
        ]

        for command in cases:
            with self.subTest(command=command):
                self.assertEqual(hook.detect_block_reasons(command), [])

    def test_pre_tool_use_blocks_and_logs_attempt(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "rm -rf ./dist"},
        }

        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"USERPROFILE": home, "HOME": home},
                check=False,
            )
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn(
                "Blocked destructive Bash command",
                hook_output["permissionDecisionReason"],
            )
            self.assertTrue(log_path.exists())
            self.assertIn("rm -rf ./dist", log_path.read_text(encoding="utf-8"))

    def test_pre_tool_use_allows_safe_command(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "cwd": "/tmp/project",
            "tool_input": {"command": "npm test"},
        }

        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
