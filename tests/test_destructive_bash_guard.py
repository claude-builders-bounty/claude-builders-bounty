import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "destructive-bash-guard.py"


def run_hook(command, *, tool_name="Bash", home=None):
    env = os.environ.copy()
    if home is not None:
        env["HOME"] = str(home)
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashGuardTests(unittest.TestCase):
    def assert_blocked(self, command, tmp_path):
        result = run_hook(command, home=tmp_path)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("destructive-bash-guard", result.stderr)
        self.assertIn('"decision": "block"', result.stdout)
        log_path = tmp_path / ".claude" / "hooks" / "blocked.log"
        self.assertTrue(log_path.exists())
        entry = json.loads(log_path.read_text().strip().splitlines()[-1])
        self.assertEqual(entry["command"], command)
        self.assertEqual(entry["project_path"], "/tmp/example-project")
        return result

    def test_blocks_rm_rf(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            self.assert_blocked("rm -rf build", tmp_path)
            self.assert_blocked("sudo rm -fr /tmp/demo", tmp_path)

    def test_blocks_dangerous_sql(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            self.assert_blocked("psql -c 'DROP TABLE users'", tmp_path)
            self.assert_blocked("mysql -e 'TRUNCATE sessions'", tmp_path)
            self.assert_blocked("psql -c 'DELETE FROM users'", tmp_path)

    def test_blocks_force_push(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            self.assert_blocked("git push --force origin main", tmp_path)
            self.assert_blocked("git push -f origin main", tmp_path)
            self.assert_blocked("git push --force-with-lease", tmp_path)

    def test_allows_safe_commands(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            safe = [
                "ls -la",
                "npm test",
                "git status --short",
                "psql -c 'SELECT * FROM users'",
                "psql -c 'DELETE FROM users WHERE id = 1'",
                "rm -r build",
                "rm -f file.txt",
            ]
            for command in safe:
                with self.subTest(command=command):
                    result = run_hook(command, home=tmp_path)
                    self.assertEqual(result.returncode, 0, command)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(result.stderr, "")

    def test_ignores_non_bash_tool(self):
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            result = run_hook("rm -rf build", tool_name="Read", home=tmp_path)
            self.assertEqual(result.returncode, 0)
            self.assertFalse((tmp_path / ".claude" / "hooks" / "blocked.log").exists())

    def test_invalid_json_fails_cleanly(self):
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not-json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid hook JSON", result.stderr)


if __name__ == "__main__":
    unittest.main()
