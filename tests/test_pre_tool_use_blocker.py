import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "hooks" / "pre-tool-use-blocker.py"
SPEC = importlib.util.spec_from_file_location("pre_tool_use_blocker", MODULE_PATH)
hook = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(hook)


def payload(command, project_path="/work/project"):
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "project_path": project_path,
    }


class PreToolUseBlockerTests(unittest.TestCase):
    def test_blocks_required_dangerous_patterns_and_logs_attempt(self):
        commands = [
            "rm -rf build",
            "psql -c 'DROP TABLE users'",
            "git push --force origin main",
            "sqlite3 app.db 'TRUNCATE TABLE sessions'",
            "psql -c 'DELETE FROM accounts'",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            for command in commands:
                result = hook.evaluate(payload(command), log_path=log_path)
                self.assertEqual(
                    result["hookSpecificOutput"]["permissionDecision"],
                    "deny",
                )

            lines = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), len(commands))
            first_event = json.loads(lines[0])
            self.assertIn("timestamp", first_event)
            self.assertEqual(first_event["attempted_command"], commands[0])
            self.assertEqual(first_event["project_path"], "/work/project")

    def test_delete_from_with_where_is_allowed(self):
        result = hook.evaluate(payload("psql -c 'DELETE FROM accounts WHERE id = 1'"))

        self.assertEqual(result, {"continue": True})

    def test_normal_bash_command_does_not_interfere(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            result = hook.evaluate(payload("git status --short"), log_path=log_path)

            self.assertEqual(result, {"continue": True})
            self.assertFalse(log_path.exists())

    def test_non_bash_tools_are_ignored(self):
        result = hook.evaluate(
            {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}
        )

        self.assertEqual(result, {"continue": True})


if __name__ == "__main__":
    unittest.main()
