import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_blocker.py"

spec = importlib.util.spec_from_file_location("pre_tool_use_blocker", HOOK)
blocker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blocker)


def payload(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/project",
        "tool_input": {"command": command},
    }


class BlockerTests(unittest.TestCase):
    def test_allows_safe_commands(self):
        self.assertIsNone(blocker.evaluate_payload(payload("npm test")))
        self.assertIsNone(blocker.evaluate_payload(payload("DELETE FROM users WHERE id = 1")))

    def test_blocks_required_patterns(self):
        commands = [
            "rm -rf /tmp/build",
            "rm -fr dist",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "psql -c 'TRUNCATE audit_log'",
            "mysql -e 'DELETE FROM users'",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(blocker.evaluate_payload(payload(command)))

    def test_cli_outputs_deny_json_and_writes_log(self):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload("rm -rf /tmp/build")),
                text=True,
                capture_output=True,
                env=env,
                check=True,
            )

            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text().strip())
            self.assertEqual(log_entry["command"], "rm -rf /tmp/build")
            self.assertEqual(log_entry["project_path"], "/tmp/project")


if __name__ == "__main__":
    unittest.main()
