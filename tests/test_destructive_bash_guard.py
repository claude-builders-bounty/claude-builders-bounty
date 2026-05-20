import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / ".claude" / "hooks" / "destructive-bash-guard.py"


spec = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DestructiveBashGuardTests(unittest.TestCase):
    def test_blocks_required_patterns(self) -> None:
        blocked = [
            "rm -rf build",
            "git push origin main --force",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users'",
        ]

        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.detect_block_reason(command))

    def test_allows_normal_commands(self) -> None:
        allowed = [
            "npm test",
            "git push origin feature-branch",
            "rm -r build",
            "echo 'rm -rf /tmp/example'",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "python - <<'PY'\nprint('DROP TABLE example')\nPY",
        ]

        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.detect_block_reason(command))

    def test_hook_outputs_deny_json_and_logs_blocked_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            payload = {
                "tool_name": "Bash",
                "cwd": "/tmp/example-project",
                "tool_input": {"command": "rm -rf /tmp/example-project"},
            }

            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            hook_output = output["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("rm -rf", hook_output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], payload["tool_input"]["command"])
            self.assertEqual(log_entry["project_path"], payload["cwd"])


if __name__ == "__main__":
    unittest.main()
