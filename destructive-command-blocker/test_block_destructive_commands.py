import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("block_destructive_commands.py")
SPEC = importlib.util.spec_from_file_location("block_destructive_commands", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def payload(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }


class DestructiveCommandBlockerTests(unittest.TestCase):
    def test_blocks_required_patterns(self):
        cases = {
            "rm -rf /tmp/example": "recursive and force",
            "rm -fr ./build": "recursive and force",
            "psql -c 'DROP TABLE users'": "DROP TABLE",
            "git push --force origin main": "force-push",
            "mysql -e 'TRUNCATE audit_log'": "TRUNCATE",
            "psql -c 'DELETE FROM users'": "DELETE FROM without a WHERE",
        }
        for command, reason in cases.items():
            with self.subTest(command=command):
                self.assertIn(reason, MODULE.find_block_reason(command))

    def test_allows_normal_commands(self):
        allowed = [
            "ls -la",
            "git push origin main",
            "rm -r ./build",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "python3 -m pytest",
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(MODULE.find_block_reason(command))

    def test_main_denies_and_logs_blocked_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            with mock.patch.object(MODULE, "BLOCKED_LOG", log_path):
                with mock.patch("sys.stdin") as stdin:
                    stdin.read.return_value = json.dumps(payload("rm -rf /tmp/example"))
                    stdin.__iter__.return_value = iter([stdin.read.return_value])
                    with mock.patch("json.load", return_value=payload("rm -rf /tmp/example")):
                        with mock.patch("builtins.print") as print_mock:
                            self.assertEqual(MODULE.main(), 0)

            output = json.loads(print_mock.call_args.args[0])
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("Blocked destructive Bash command", decision["permissionDecisionReason"])
            self.assertIn("rm -rf /tmp/example", log_path.read_text(encoding="utf-8"))

    def test_script_allows_non_bash_payload_without_output(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps({"hook_event_name": "PreToolUse", "tool_name": "Read"}),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout, "")
        self.assertEqual(proc.stderr, "")


if __name__ == "__main__":
    unittest.main()
