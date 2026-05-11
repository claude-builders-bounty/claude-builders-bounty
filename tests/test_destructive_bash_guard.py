import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK = REPO_ROOT / ".claude" / "hooks" / "block_destructive_bash.py"


def run_hook(command, home, tool_name="Bash"):
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/workspace/project",
    }
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )


class DestructiveBashGuardTests(unittest.TestCase):
    def test_allows_normal_bash_commands(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("git status && python -m unittest", Path(tmp))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, "")
            self.assertFalse((Path(tmp) / ".claude" / "hooks" / "blocked.log").exists())

    def test_allows_non_bash_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("rm -rf build", Path(tmp), tool_name="Read")
            self.assertEqual(result.returncode, 0)

    def test_blocks_rm_rf_and_logs_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = run_hook("sudo rm -rf build", home)
            self.assertEqual(result.returncode, 2)
            self.assertIn("Blocked Bash command", result.stderr)
            log_path = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            entry = json.loads(log_path.read_text().splitlines()[0])
            self.assertEqual(entry["reason"], "rm -rf style recursive forced deletion")
            self.assertEqual(entry["command"], "sudo rm -rf build")
            self.assertEqual(entry["project_path"], "/workspace/project")

    def test_blocks_git_force_push(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_hook("git push origin main --force-with-lease", Path(tmp))
            self.assertEqual(result.returncode, 2)
            self.assertIn("git push force flag", result.stderr)

    def test_blocks_drop_table_and_truncate(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_hook('psql -c "DROP TABLE users"', Path(tmp)).returncode, 2)
            self.assertEqual(run_hook('psql -c "TRUNCATE events"', Path(tmp)).returncode, 2)

    def test_blocks_delete_without_where_but_allows_where(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            self.assertEqual(run_hook('psql -c "DELETE FROM users"', home).returncode, 2)
            self.assertEqual(run_hook('psql -c "DELETE FROM users WHERE id = 1"', home).returncode, 0)

    def test_install_writes_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["HOME"] = tmp
            result = subprocess.run(
                [sys.executable, str(HOOK), "--install"],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            settings = json.loads((Path(tmp) / ".claude" / "settings.json").read_text())
            pre_tool_hooks = settings["hooks"]["PreToolUse"]
            self.assertEqual(pre_tool_hooks[0]["matcher"], "Bash")
            self.assertIn("block_destructive_bash.py", pre_tool_hooks[0]["hooks"][0]["command"])


if __name__ == "__main__":
    unittest.main()
