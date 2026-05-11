import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).with_name("destructive_command_blocker.py")


def run_hook(command: str, cwd: str = "/tmp/example-project") -> subprocess.CompletedProcess:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }

    env = os.environ.copy()
    env["CLAUDE_HOOKS_HOME"] = tempfile.mkdtemp(prefix="claude-hooks-test-")

    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveCommandBlockerTests(unittest.TestCase):
    def test_allows_normal_bash_command(self) -> None:
        result = run_hook("npm test")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")

    def test_blocks_rm_rf(self) -> None:
        result = run_hook("rm -rf build")

        self.assertEqual(result.returncode, 2)
        self.assertIn("rm -rf", result.stderr)
        self.assertIn("destructive", result.stderr.lower())

    def test_blocks_rm_recursive_force_split_across_flags(self) -> None:
        result = run_hook("rm -r -f build")

        self.assertEqual(result.returncode, 2)
        self.assertIn("recursive", result.stderr.lower())

    def test_blocks_force_push(self) -> None:
        result = run_hook("git push --force origin main")

        self.assertEqual(result.returncode, 2)
        self.assertIn("git push --force", result.stderr)

    def test_blocks_table_drop_and_truncate(self) -> None:
        for command in ("psql -c 'DROP TABLE users'", "mysql -e 'TRUNCATE sessions'"):
            with self.subTest(command=command):
                result = run_hook(command)
                self.assertEqual(result.returncode, 2)

    def test_blocks_delete_from_without_where(self) -> None:
        result = run_hook("psql -c 'DELETE FROM users'")

        self.assertEqual(result.returncode, 2)
        self.assertIn("DELETE FROM without WHERE", result.stderr)

    def test_allows_delete_from_with_where(self) -> None:
        result = run_hook("psql -c 'DELETE FROM users WHERE id = 1'")

        self.assertEqual(result.returncode, 0)

    def test_logs_blocked_attempt(self) -> None:
        hooks_home = tempfile.mkdtemp(prefix="claude-hooks-test-")
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /tmp/example"},
            "cwd": "/work/project",
        }

        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env={**os.environ, "CLAUDE_HOOKS_HOME": hooks_home},
            check=False,
        )

        log_path = Path(hooks_home) / "hooks" / "blocked.log"
        self.assertEqual(result.returncode, 2)
        self.assertTrue(log_path.exists())
        log = log_path.read_text(encoding="utf-8")
        self.assertIn("rm -rf /tmp/example", log)
        self.assertIn("/work/project", log)


if __name__ == "__main__":
    unittest.main()
