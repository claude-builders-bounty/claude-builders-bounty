import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HOOK_PATH = Path(__file__).resolve().parents[1] / "block-destructive-bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def bash_event(command: str, cwd: str = "/tmp/example") -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": cwd,
    }


class DetectionTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self):
        self.assertIsNotNone(MODULE.find_block_reason("rm -rf build"))
        self.assertIsNotNone(MODULE.find_block_reason("rm -fr build"))
        self.assertIsNotNone(MODULE.find_block_reason("rm -r build -f"))

    def test_blocks_forced_push(self):
        self.assertIsNotNone(MODULE.find_block_reason("git push --force origin main"))
        self.assertIsNotNone(
            MODULE.find_block_reason("git push --force-with-lease origin main")
        )

    def test_blocks_database_destructive_operations(self):
        self.assertIsNotNone(MODULE.find_block_reason("DROP TABLE users"))
        self.assertIsNotNone(MODULE.find_block_reason("TRUNCATE TABLE users"))
        self.assertIsNotNone(
            MODULE.find_block_reason('sqlite3 app.db "DELETE FROM users"')
        )

    def test_allows_delete_with_where(self):
        self.assertIsNone(
            MODULE.find_block_reason('sqlite3 app.db "DELETE FROM users WHERE id = 1"')
        )

    def test_allows_read_only_commands_containing_phrases(self):
        safe_commands = [
            'echo "rm -rf is dangerous"',
            'grep "DELETE FROM" migration.sql',
            "git diff -- 'docs/DROP TABLE.md'",
            "cat notes.txt",
            "ls -la",
        ]
        for command in safe_commands:
            with self.subTest(command=command):
                self.assertIsNone(MODULE.find_block_reason(command))

    def test_chained_command_still_blocks_the_dangerous_segment(self):
        self.assertIsNotNone(MODULE.find_block_reason("git status && rm -rf build"))

    def test_non_bash_events_are_ignored(self):
        self.assertIsNone(MODULE.evaluate_event({"tool_name": "Read"}))


class HookProcessTests(unittest.TestCase):
    def run_hook(self, event: dict, log_path: Path):
        completed = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(event),
            text=True,
            capture_output=True,
            env={**os.environ, MODULE.LOG_ENV_VAR: str(log_path)},
        )
        return completed

    def test_blocked_event_returns_deny_payload_and_writes_log(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "blocked.log"
            completed = self.run_hook(bash_event("rm -rf build"), log_path)

            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            decision = payload["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["permissionDecisionReason"])

            records = [json.loads(line) for line in log_path.read_text().splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["command"], "rm -rf build")
            self.assertEqual(records[0]["cwd"], "/tmp/example")

    def test_allowed_event_is_silent_and_has_zero_exit_status(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "blocked.log"
            completed = self.run_hook(bash_event("git status"), log_path)

            self.assertEqual(completed.returncode, 0)
            self.assertEqual(completed.stdout, "")
            self.assertFalse(log_path.exists())

    def test_malformed_input_fails_open(self):
        completed = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="{not-json",
            text=True,
            capture_output=True,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
