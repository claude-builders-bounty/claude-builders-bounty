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

spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(hook)


def event(command):
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(ROOT),
    }


class DestructiveBashHookTest(unittest.TestCase):
    def test_detects_required_destructive_patterns(self):
        commands = [
            "rm -rf build",
            "bash -lc 'rm -rf build'",
            "git push --force origin main",
            "psql -c 'DROP TABLE users'",
            "mysql -e 'TRUNCATE sessions'",
            "sqlite3 app.db 'DELETE FROM users'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(hook.detect_dangerous_command(command))

    def test_allows_normal_bash_commands(self):
        commands = [
            "ls -la",
            "git status",
            "python -m unittest",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 1'",
        ]

        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(hook.detect_dangerous_command(command), [])

    def test_process_event_returns_pretooluse_denial_and_logs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"

            output = hook.process_event(event("rm -rf tmp"), log_path)

            self.assertEqual(output["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("rm command", output["hookSpecificOutput"]["permissionDecisionReason"])

            logged = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(logged["attempted_command"], "rm -rf tmp")
            self.assertEqual(logged["project_path"], str(ROOT))

    def test_cli_outputs_valid_json_for_blocked_command(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env["HOME"] = temp_dir
            env["USERPROFILE"] = temp_dir

            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(event("git push -f origin main")),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )

            output = json.loads(result.stdout)
            self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
