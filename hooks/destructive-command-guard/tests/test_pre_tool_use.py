import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "pre_tool_use.py"
SPEC = importlib.util.spec_from_file_location("pre_tool_use", MODULE_PATH)
pre_tool_use = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["pre_tool_use"] = pre_tool_use
SPEC.loader.exec_module(pre_tool_use)


class DestructiveCommandGuardTests(unittest.TestCase):
    def test_blocks_rm_recursive_force_variants(self):
        dangerous = [
            "rm -rf build",
            "rm -fr build",
            "rm -r -f build",
            "sudo rm -Rf /tmp/demo",
            "env FOO=bar rm -f -r ./cache",
        ]

        for command in dangerous:
            with self.subTest(command=command):
                decision = pre_tool_use.detect_block(command)
                self.assertIsNotNone(decision)
                self.assertEqual(decision.rule, "rm-rf")

    def test_blocks_force_push_variants(self):
        dangerous = [
            "git push --force origin main",
            "git push -f",
            "git push --force-with-lease origin main",
            "FOO=bar git push --force=origin main",
        ]

        for command in dangerous:
            with self.subTest(command=command):
                decision = pre_tool_use.detect_block(command)
                self.assertIsNotNone(decision)
                self.assertEqual(decision.rule, "git-force-push")

    def test_blocks_sql_destructive_patterns(self):
        cases = {
            "psql -c 'DROP TABLE users'": "drop-table",
            "sqlite3 app.db 'TRUNCATE sessions'": "truncate",
            "psql -c 'DELETE FROM users;'": "delete-without-where",
            "mysql -e \"delete from accounts\"": "delete-without-where",
        }

        for command, rule in cases.items():
            with self.subTest(command=command):
                decision = pre_tool_use.detect_block(command)
                self.assertIsNotNone(decision)
                self.assertEqual(decision.rule, rule)

    def test_allows_normal_commands(self):
        safe = [
            "npm test",
            "git push origin main",
            "rm build.log",
            "psql -c 'DELETE FROM users WHERE id = 1;'",
            "sqlite3 app.db 'select * from users'",
        ]

        for command in safe:
            with self.subTest(command=command):
                self.assertIsNone(pre_tool_use.detect_block(command))

    def test_logs_blocked_attempt_as_json_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "blocked.log"
            decision = pre_tool_use.BlockDecision("rm-rf", "Blocked test")

            with patch.object(pre_tool_use, "LOG_PATH", log_path):
                pre_tool_use.log_block("rm -rf build", decision, "/repo")

            entry = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertIn("timestamp", entry)
            self.assertEqual(entry["attempted_command"], "rm -rf build")
            self.assertEqual(entry["project_path"], "/repo")
            self.assertEqual(entry["rule"], "rm-rf")

    def test_denies_with_claude_code_pre_tool_use_json(self):
        decision = pre_tool_use.BlockDecision("truncate", "Blocked TRUNCATE")
        output = pre_tool_use.deny_output(decision)

        self.assertEqual(
            output["hookSpecificOutput"]["hookEventName"],
            "PreToolUse",
        )
        self.assertEqual(
            output["hookSpecificOutput"]["permissionDecision"],
            "deny",
        )
        self.assertIn("Blocked TRUNCATE", json.dumps(output))


if __name__ == "__main__":
    unittest.main()
