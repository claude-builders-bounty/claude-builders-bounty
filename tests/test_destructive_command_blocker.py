import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "hooks"
    / "destructive-command-blocker"
    / "block_destructive_commands.py"
)

SPEC = importlib.util.spec_from_file_location("block_destructive_commands", MODULE_PATH)
blocker = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(blocker)


class DestructiveCommandBlockerTests(unittest.TestCase):
    def payload(self, command):
        return {
            "tool_name": "Bash",
            "tool_input": {"command": command},
            "cwd": "/tmp/example-project",
        }

    def assert_blocked(self, command):
        with mock.patch.object(blocker, "log_blocked_attempt") as log_attempt:
            with mock.patch("builtins.print") as print_mock:
                result = blocker.run(self.payload(command))

        self.assertEqual(result, 0)
        log_attempt.assert_called_once_with(command, "/tmp/example-project")
        output = json.loads(print_mock.call_args.args[0])
        self.assertEqual(output["decision"], "block")

    def assert_allowed(self, command):
        with mock.patch.object(blocker, "log_blocked_attempt") as log_attempt:
            with mock.patch("builtins.print") as print_mock:
                result = blocker.run(self.payload(command))

        self.assertEqual(result, 0)
        log_attempt.assert_not_called()
        output = json.loads(print_mock.call_args.args[0])
        self.assertEqual(output["decision"], "approve")

    def test_blocks_rm_rf_variants(self):
        self.assert_blocked("rm -rf dist")
        self.assert_blocked("rm -fr ./tmp")

    def test_blocks_destructive_sql(self):
        self.assert_blocked("psql -c 'DROP TABLE users'")
        self.assert_blocked("mysql -e 'TRUNCATE sessions'")
        self.assert_blocked("psql -c 'DELETE FROM accounts'")
        self.assert_blocked("psql -c 'DELETE FROM accounts; SELECT * FROM logs WHERE id = 1'")

    def test_blocks_force_push(self):
        self.assert_blocked("git push origin main --force")
        self.assert_blocked("git push --force-with-lease origin main")

    def test_allows_normal_commands(self):
        self.assert_allowed("ls -la")
        self.assert_allowed("git push origin main")
        self.assert_allowed("psql -c 'DELETE FROM accounts WHERE id = 1'")

    def test_ignores_non_bash_tools(self):
        payload = {"tool_name": "Read", "tool_input": {"file_path": "README.md"}}

        with mock.patch.object(blocker, "log_blocked_attempt") as log_attempt:
            with mock.patch("builtins.print") as print_mock:
                result = blocker.run(payload)

        self.assertEqual(result, 0)
        log_attempt.assert_not_called()
        output = json.loads(print_mock.call_args.args[0])
        self.assertEqual(output["decision"], "approve")


if __name__ == "__main__":
    unittest.main()
