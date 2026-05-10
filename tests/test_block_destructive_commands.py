import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_commands.py"

spec = importlib.util.spec_from_file_location("block_destructive_commands", HOOK)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class BlockDestructiveCommandsTest(unittest.TestCase):
    def test_blocks_required_patterns(self):
        blocked = [
            "rm -rf build/",
            "rm -fr /tmp/example",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "git -C repo push --force-with-lease origin main",
            "TRUNCATE TABLE audit_logs",
            "DELETE FROM users",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(module.find_block_reason(command))

    def test_allows_safe_commands(self):
        allowed = [
            "rm build/output.txt",
            "git push origin main",
            "SELECT * FROM users",
            "DELETE FROM users WHERE id = 1",
            "python -m pytest",
            "npm run build",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(module.find_block_reason(command))

    def test_extract_command_from_claude_payload_shape(self):
        payload = {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git push --force",
            },
        }

        self.assertEqual(module.extract_command(payload), "git push --force")

    def test_script_exits_2_and_writes_stderr_for_blocked_command(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            home = Path(tmp_dir) / "home"
            home.mkdir()

            payload = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": "DELETE FROM sessions",
                    "cwd": "/tmp/project",
                },
            }

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["USERPROFILE"] = str(home)

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "DELETE FROM statements must include a WHERE clause",
                result.stderr,
            )

            log_path = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_record = json.loads(log_path.read_text().splitlines()[0])
            self.assertEqual(log_record["command"], "DELETE FROM sessions")
            self.assertEqual(log_record["project_path"], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
