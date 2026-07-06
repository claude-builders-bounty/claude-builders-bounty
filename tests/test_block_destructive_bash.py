import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / ".claude" / "hooks" / "block_destructive_bash.py"


def load_hook():
    spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BlockDestructiveBashTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hook = load_hook()

    def test_blocks_rm_rf_variants(self):
        for command in ["rm -rf tmp", "rm -fr tmp", "rm -r -f tmp"]:
            with self.subTest(command=command):
                self.assertIn("rm", self.hook.detect_block_reason(command))

    def test_blocks_nested_shell_rm_rf(self):
        reason = self.hook.detect_block_reason('bash -c "rm -rf /tmp/build"')
        self.assertIn("rm", reason)

    def test_blocks_force_push(self):
        for command in ["git push --force", "git push -f origin main"]:
            with self.subTest(command=command):
                self.assertIn("git push", self.hook.detect_block_reason(command))

    def test_blocks_destructive_sql(self):
        self.assertEqual(
            self.hook.detect_block_reason("psql -c 'DROP TABLE users'"),
            "DROP TABLE statement",
        )
        self.assertEqual(
            self.hook.detect_block_reason("mysql -e 'DELETE FROM users'"),
            "DELETE FROM statement without a WHERE clause",
        )
        self.assertEqual(
            self.hook.detect_block_reason("sqlite3 db 'TRUNCATE TABLE sessions'"),
            "TRUNCATE statement",
        )

    def test_allows_normal_commands(self):
        allowed = [
            "npm test",
            "git status",
            "rm build.log",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            'echo "rm -rf is dangerous"',
        ]
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(self.hook.detect_block_reason(command))

    def test_hook_outputs_deny_json_and_writes_log(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf tmp"},
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
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("rm", decision["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            record = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(record["command"], "rm -rf tmp")
            self.assertEqual(record["project_path"], "/tmp/example-project")


if __name__ == "__main__":
    unittest.main()
