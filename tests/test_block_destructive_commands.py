import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "hooks" / "pre_tool_use" / "block_destructive_commands.py"


def load_module():
    spec = importlib.util.spec_from_file_location("block_destructive_commands", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class BlockDestructiveCommandsTests(unittest.TestCase):
    def test_blocks_rm_rf_and_logs_attempt(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf ./build"},
                "cwd": "/tmp/project-alpha",
            }

            stdout = io.StringIO()
            exit_code = module.main(
                stdin=io.StringIO(json.dumps(payload)),
                stdout=stdout,
                log_path=log_path,
            )

            self.assertEqual(exit_code, 0)
            response = json.loads(stdout.getvalue())
            self.assertEqual(response["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("rm -rf", response["hookSpecificOutput"]["permissionDecisionReason"])
            logged = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(logged["project_path"], "/tmp/project-alpha")
            self.assertEqual(logged["command"], "rm -rf ./build")

    def test_allows_safe_commands_without_creating_log(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "cwd": "/tmp/project-beta",
            }

            stdout = io.StringIO()
            exit_code = module.main(
                stdin=io.StringIO(json.dumps(payload)),
                stdout=stdout,
                log_path=log_path,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertFalse(log_path.exists())

    def test_blocks_delete_without_where_clause(self):
        module = load_module()
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "psql -c \"DELETE FROM users;\""},
            "cwd": "/tmp/project-gamma",
        }

        stdout = io.StringIO()
        exit_code = module.main(
            stdin=io.StringIO(json.dumps(payload)),
            stdout=stdout,
            log_path=Path(tempfile.gettempdir()) / "unused-blocked.log",
        )

        self.assertEqual(exit_code, 0)
        response = json.loads(stdout.getvalue())
        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("DELETE FROM", response["hookSpecificOutput"]["permissionDecisionReason"])

    def test_blocks_git_push_force(self):
        module = load_module()
        payload = {
            "tool_name": "Bash",
            "tool_input": {"command": "git push --force origin main"},
            "cwd": "/tmp/project-delta",
        }

        stdout = io.StringIO()
        exit_code = module.main(
            stdin=io.StringIO(json.dumps(payload)),
            stdout=stdout,
            log_path=Path(tempfile.gettempdir()) / "unused-force.log",
        )

        self.assertEqual(exit_code, 0)
        response = json.loads(stdout.getvalue())
        self.assertEqual(response["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("git push --force", response["hookSpecificOutput"]["permissionDecisionReason"])

    def test_allows_delete_with_where_clause(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "psql -c \"DELETE FROM users WHERE id = 42;\""},
                "cwd": "/tmp/project-epsilon",
            }

            stdout = io.StringIO()
            exit_code = module.main(
                stdin=io.StringIO(json.dumps(payload)),
                stdout=stdout,
                log_path=log_path,
            )

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue(), "")
            self.assertFalse(log_path.exists())


if __name__ == "__main__":
    unittest.main()
