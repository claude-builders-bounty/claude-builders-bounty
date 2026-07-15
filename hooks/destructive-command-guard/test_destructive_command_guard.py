import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("destructive_command_guard.py")


def run_hook(payload: str, home: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=payload,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveCommandGuardTest(unittest.TestCase):
    def test_allows_normal_commands(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            result = run_hook('{"tool_input":{"command":"npm test"},"cwd":"/repo"}', home_path)

            self.assertEqual(result.returncode, 0)
            self.assertFalse((home_path / ".claude/hooks/blocked.log").exists())

    def test_blocks_rm_rf_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            home_path = Path(home)
            result = run_hook('{"tool_input":{"command":"rm -rf .next"},"cwd":"/repo"}', home_path)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked dangerous Bash command", result.stderr)
            log = (home_path / ".claude/hooks/blocked.log").read_text()
            self.assertIn("/repo", log)
            self.assertIn("recursive forced removal", log)
            self.assertIn("rm -rf .next", log)

    def test_blocks_delete_from_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(
                '{"tool_input":{"command":"sqlite3 app.db \\"DELETE FROM users;\\""},"cwd":"/repo"}',
                Path(home),
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("DELETE FROM without WHERE", result.stderr)

    def test_allows_delete_from_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(
                '{"tool_input":{"command":"sqlite3 app.db \\"DELETE FROM users WHERE id = 1;\\""},"cwd":"/repo"}',
                Path(home),
            )

            self.assertEqual(result.returncode, 0)

    def test_blocks_force_push(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_hook('{"tool_input":{"command":"git push origin main --force"},"cwd":"/repo"}', Path(home))

            self.assertEqual(result.returncode, 2)
            self.assertIn("force pushing", result.stderr)


if __name__ == "__main__":
    unittest.main()
