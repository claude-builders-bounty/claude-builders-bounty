import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_bash.py"

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BlockDestructiveBashTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        bad_commands = [
            "rm -rf /tmp/build",
            "sudo rm -fr /var/tmp/cache",
            "psql -c 'DROP TABLE users'",
            "git push origin main --force",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "TRUNCATE audit_log",
            "DELETE FROM users;",
            "DELETE FROM users\n",
        ]
        for command in bad_commands:
            with self.subTest(command=command):
                self.assertIsNotNone(module.find_block_reason(command))

    def test_allows_normal_commands(self):
        good_commands = [
            "npm test",
            "rm -r ./dist",
            "git push origin feature-branch",
            "SELECT * FROM users",
            "DELETE FROM users WHERE id = 123;",
            "python3 manage.py migrate",
        ]
        for command in good_commands:
            with self.subTest(command=command):
                self.assertIsNone(module.find_block_reason(command))

    def test_hook_denies_and_logs(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "DELETE FROM sessions;"},
                "cwd": "/tmp/example-project",
            }
            proc = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            response = json.loads(proc.stdout)
            output = response["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("DELETE FROM without WHERE", output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            entry = json.loads(log_path.read_text().strip())
            self.assertEqual(entry["project_path"], "/tmp/example-project")
            self.assertEqual(entry["command"], "DELETE FROM sessions;")

    def test_non_bash_tool_is_ignored(self):
        payload = {"tool_name": "Read", "tool_input": {"command": "rm -rf /"}}
        proc = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
