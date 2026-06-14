import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_bash.py"


def run_hook(command):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
    }
    env = os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="claude-hook-test-") as temp_home:
        env["CLAUDE_BLOCK_LOG"] = str(Path(temp_home) / "blocked.log")
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )
        log_path = Path(env["CLAUDE_BLOCK_LOG"])
        log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        return result, log_text


class BlockDestructiveBashTest(unittest.TestCase):
    def assert_blocked(self, command):
        result, log_text = run_hook(command)
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertTrue(decision["permissionDecisionReason"])
        entry = json.loads(log_text)
        self.assertEqual(entry["attempted_command"], command)
        self.assertEqual(entry["project_path"], "/tmp/example-project")
        self.assertIn("timestamp", entry)

    def test_blocks_destructive_patterns(self):
        blocked = [
            "rm -rf dist",
            "rm -r -f dist",
            "rm -f -r dist",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "git push -f origin main",
            "mysql -e 'TRUNCATE sessions'",
            "psql -c 'DELETE FROM users'",
        ]
        for command in blocked:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_allows_normal_bash_commands(self):
        allowed = [
            "npm test",
            "git status --short",
            "rm dist/app.js",
            "psql -c 'DELETE FROM users WHERE id = 1'",
        ]
        for command in allowed:
            with self.subTest(command=command):
                result, log_text = run_hook(command)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
                self.assertEqual(log_text, "")

    def test_installer_is_idempotent_and_preserves_settings(self):
        installer = HOOK.parents[0] / "install.py"
        with tempfile.TemporaryDirectory(prefix="claude-install-test-") as temp_home:
            claude_home = Path(temp_home) / ".claude"
            claude_home.mkdir()
            settings = claude_home / "settings.json"
            settings.write_text('{"theme": "dark"}\n', encoding="utf-8")
            env = os.environ.copy()
            env["CLAUDE_HOME"] = str(claude_home)

            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(installer)],
                    text=True,
                    capture_output=True,
                    check=False,
                    env=env,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            installed = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(installed["theme"], "dark")
            self.assertEqual(len(installed["hooks"]["PreToolUse"]), 1)
            self.assertTrue((claude_home / "hooks" / HOOK.name).exists())


if __name__ == "__main__":
    unittest.main()
