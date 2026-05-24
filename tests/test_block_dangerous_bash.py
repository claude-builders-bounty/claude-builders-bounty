import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "block-dangerous-bash.py"


class BlockDangerousBashHookTest(unittest.TestCase):
    def run_hook(self, command: str, *, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }
        env = os.environ.copy()
        env["HOME"] = self.home

        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = self.tempdir.name

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def blocked_log_entries(self) -> list[dict]:
        log_path = Path(self.home) / ".claude" / "hooks" / "blocked.log"
        return [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]

    def test_allows_normal_bash_commands(self) -> None:
        for command in ["ls -la", "git status", "rm -f scratch.txt", "echo 'rm -rf /tmp/example'"]:
            with self.subTest(command=command):
                result = self.run_hook(command)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_rm_rf_variants_and_logs_attempt(self) -> None:
        result = self.run_hook("sudo rm -fr build")

        self.assertEqual(result.returncode, 2)
        self.assertIn("Blocked dangerous Bash command", result.stderr)
        entry = self.blocked_log_entries()[0]
        self.assertEqual(entry["attempted_command"], "sudo rm -fr build")
        self.assertEqual(entry["project_path"], "/tmp/example-project")
        self.assertIn("timestamp", entry)

    def test_blocks_drop_table(self) -> None:
        result = self.run_hook('psql -c "DROP TABLE users;"')

        self.assertEqual(result.returncode, 2)
        self.assertIn("DROP TABLE", result.stderr)

    def test_blocks_truncate(self) -> None:
        result = self.run_hook('mysql -e "TRUNCATE TABLE sessions;"')

        self.assertEqual(result.returncode, 2)
        self.assertIn("TRUNCATE", result.stderr)

    def test_blocks_delete_from_without_where(self) -> None:
        result = self.run_hook('psql -c "DELETE FROM users;"')

        self.assertEqual(result.returncode, 2)
        self.assertIn("DELETE FROM without WHERE", result.stderr)

    def test_allows_delete_from_with_where(self) -> None:
        result = self.run_hook('psql -c "DELETE FROM users WHERE id = 7;"')

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_blocks_git_push_force(self) -> None:
        result = self.run_hook("git push --force origin main")

        self.assertEqual(result.returncode, 2)
        self.assertIn("git push --force", result.stderr)

    def test_ignores_non_bash_tools(self) -> None:
        result = self.run_hook("rm -rf build", tool_name="Read")

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
