import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "claude_destructive_command_hook.py"


def run_hook(payload, home):
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
    )


def bash_payload(command, project_dir="/tmp/project"):
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "project_dir": project_dir,
    }


class DestructiveCommandHookTest(unittest.TestCase):
    def test_blocks_rm_rf_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            result = run_hook(bash_payload("rm -rf build"), home)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked destructive command", result.stdout)

            log_file = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_file.exists())
            log = log_file.read_text()
            self.assertIn("rm -rf build", log)
            self.assertIn("/tmp/project", log)

    def test_blocks_git_push_force(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("git push --force origin main"), Path(home))

            self.assertEqual(result.returncode, 2)
            self.assertIn("git push --force", result.stdout)

    def test_blocks_drop_table_and_truncate(self):
        with tempfile.TemporaryDirectory() as home:
            home = Path(home)
            for command in ["psql -c 'DROP TABLE users'", "mysql -e 'TRUNCATE sessions'"]:
                result = run_hook(bash_payload(command), home)
                self.assertEqual(result.returncode, 2)

    def test_blocks_delete_from_without_where(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("psql -c 'DELETE FROM users'"), Path(home))

            self.assertEqual(result.returncode, 2)
            self.assertIn("DELETE FROM without WHERE", result.stdout)

    def test_allows_delete_from_with_where(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("psql -c 'DELETE FROM users WHERE id = 1'"), Path(home))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_allows_normal_bash_command(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook(bash_payload("python3 -m unittest"), Path(home))

            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_ignores_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as home:
            result = run_hook({"tool_name": "Read", "tool_input": {"file_path": "README.md"}}, Path(home))

            self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
