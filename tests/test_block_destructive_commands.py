import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "hooks" / "block_destructive_commands.py"


def load_hook_module():
    spec = importlib.util.spec_from_file_location("block_destructive_commands", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class BlockDestructiveCommandsHookTest(unittest.TestCase):
    def test_hook_script_exists(self):
        self.assertTrue(HOOK_PATH.exists(), "hook script should exist")

    def test_blocks_required_dangerous_patterns(self):
        hook = load_hook_module()
        cases = [
            "rm -rf /tmp/build",
            "sudo rm -r -f /tmp/build",
            "rm --recursive --force /tmp/build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM accounts'",
        ]

        for command in cases:
            with self.subTest(command=command):
                reason = hook.find_block_reason(command)
                self.assertIsNotNone(reason)

    def test_allows_delete_from_with_where_clause(self):
        hook = load_hook_module()

        reason = hook.find_block_reason("psql -c \"DELETE FROM accounts WHERE id = 42\"")

        self.assertIsNone(reason)

    def test_allows_normal_bash_commands(self):
        hook = load_hook_module()

        reason = hook.find_block_reason("git status --short && npm test")

        self.assertIsNone(reason)

    def test_pretooluse_denial_logs_attempt_and_returns_json(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf build"},
            "cwd": "/tmp/example-project",
        }

        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_entry = log_path.read_text(encoding="utf-8")
            self.assertIn("rm -rf build", log_entry)
            self.assertIn("/tmp/example-project", log_entry)

    def test_non_bash_or_safe_payload_does_not_block(self):
        hook = load_hook_module()
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
            "cwd": "/tmp/example-project",
        }

        decision = hook.evaluate_payload(payload)

        self.assertIsNone(decision)
