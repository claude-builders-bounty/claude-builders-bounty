import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "pre_tool_use_block_dangerous_bash.py"


class DangerousBashHookTests(unittest.TestCase):
    def run_hook(self, payload):
        with tempfile.TemporaryDirectory() as home:
            env = os.environ.copy()
            env["HOME"] = home
            env["USERPROFILE"] = home

            result = subprocess.run(
                [sys.executable, str(HOOK)],
                input=json.dumps(payload),
                text=True,
                capture_output=True,
                env=env,
                cwd=ROOT,
            )

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_text = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
            return result, log_text

    def bash_payload(self, command, cwd="F:/work/project"):
        return {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": cwd,
        }

    def test_blocks_rm_rf_and_logs_attempt(self):
        result, log_text = self.run_hook(self.bash_payload("rm -rf dist"))

        self.assertEqual(result.returncode, 2)
        self.assertIn("Blocked destructive Bash command", result.stderr)
        self.assertIn("rm -rf dist", result.stderr)
        self.assertIn("rm -rf dist", log_text)
        self.assertIn("F:/work/project", log_text)

    def test_blocks_sql_destructive_patterns_case_insensitively(self):
        for command in [
            'psql -c "DROP TABLE users"',
            'mysql -e "TRUNCATE audit_log"',
            'sqlite3 app.db "DELETE FROM sessions"',
        ]:
            with self.subTest(command=command):
                result, _ = self.run_hook(self.bash_payload(command))
                self.assertEqual(result.returncode, 2)
                self.assertIn("Blocked destructive Bash command", result.stderr)

    def test_allows_delete_from_with_where_clause(self):
        result, log_text = self.run_hook(
            self.bash_payload('psql -c "DELETE FROM sessions WHERE expires_at < now()"')
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(log_text, "")

    def test_allows_normal_bash_commands(self):
        result, log_text = self.run_hook(self.bash_payload("npm test"))

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(log_text, "")

    def test_ignores_non_bash_tools(self):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Read",
            "tool_input": {"file_path": "README.md"},
            "cwd": "F:/work/project",
        }

        result, log_text = self.run_hook(payload)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(log_text, "")


if __name__ == "__main__":
    unittest.main()
