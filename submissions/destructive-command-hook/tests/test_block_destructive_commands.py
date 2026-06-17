import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_commands.py"


def run_hook(command: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    home = Path(tempfile.mkdtemp())
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    env["CLAUDE_PROJECT_DIR"] = "/tmp/example-saas"
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    return result, home


class BlockDestructiveCommandsTest(unittest.TestCase):
    def tearDown(self) -> None:
        home = getattr(self, "_last_home", None)
        if home is not None:
            shutil.rmtree(home, ignore_errors=True)

    def run_hook(self, command: str) -> tuple[subprocess.CompletedProcess[str], Path]:
        result, home = run_hook(command)
        self._last_home = home
        return result, home

    def assert_blocked(self, command: str, expected_fragment: str) -> None:
        result, home = self.run_hook(command)
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response["decision"], "block")
        self.assertIn(expected_fragment, response["reason"])

        log_path = home / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_path.exists())
        event = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(event["command"], command)
        self.assertEqual(event["project_path"], "/tmp/example-saas")

    def test_allows_normal_commands(self) -> None:
        result, home = self.run_hook("npm test && ls src")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_rm_rf(self) -> None:
        self.assert_blocked("rm -rf node_modules", "rm -rf")

    def test_blocks_split_rm_flags(self) -> None:
        self.assert_blocked("rm -r -f node_modules", "rm -rf")

    def test_blocks_long_rm_flags(self) -> None:
        self.assert_blocked("rm --recursive --force node_modules", "rm -rf")

    def test_blocks_drop_table(self) -> None:
        self.assert_blocked("sqlite3 app.db 'DROP TABLE users;'", "DROP TABLE")

    def test_blocks_truncate(self) -> None:
        self.assert_blocked("psql -c 'TRUNCATE TABLE sessions;'", "TRUNCATE")

    def test_blocks_delete_from_without_where(self) -> None:
        self.assert_blocked("psql -c 'DELETE FROM users;'", "DELETE FROM")

    def test_allows_delete_from_with_where(self) -> None:
        result, _home = self.run_hook("psql -c 'DELETE FROM users WHERE id = 1;'")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_blocks_git_push_force(self) -> None:
        self.assert_blocked("git push --force-with-lease origin main", "force-pushing")


if __name__ == "__main__":
    unittest.main()
