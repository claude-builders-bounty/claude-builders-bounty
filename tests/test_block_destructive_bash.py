import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


def run_hook(command: str, project_path: str | None = None) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": project_path or os.getcwd(),
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


class BlockDestructiveBashHookTests(unittest.TestCase):
    def test_blocks_rm_rf_and_logs_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as project:
            os.environ["HOME"] = home
            result = run_hook("rm -rf ./dist", project)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked dangerous Bash command", result.stderr)
            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf ./dist", log)
            self.assertIn(project, log)

    def test_blocks_delete_from_without_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            result = run_hook("sqlite3 app.db 'DELETE FROM users;'")

            self.assertEqual(result.returncode, 2)
            self.assertIn("DELETE FROM without a WHERE clause", result.stderr)

    def test_blocks_drop_table_truncate_and_force_push(self) -> None:
        dangerous_commands = {
            "psql app -c 'DROP TABLE users;'": "DROP TABLE",
            "mysql app -e 'TRUNCATE sessions;'": "TRUNCATE",
            "git push --force origin main": "git push --force",
        }
        for command, reason in dangerous_commands.items():
            with self.subTest(command=command), tempfile.TemporaryDirectory() as home:
                os.environ["HOME"] = home
                result = run_hook(command)

                self.assertEqual(result.returncode, 2)
                self.assertIn(reason, result.stderr)

    def test_allows_delete_from_with_where(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            result = run_hook("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'")

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")

    def test_allows_normal_bash_commands(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            os.environ["HOME"] = home
            result = run_hook("pnpm test && git status --short")

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
