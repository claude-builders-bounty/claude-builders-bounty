from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pre_tool_use


def bash_payload(command: str) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {
            "command": command,
            "cwd": "/workspace/example",
        },
    }


class DestructiveBashGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.tmpdir.name) / "blocked.log"
        self.log_patch = patch.object(pre_tool_use, "LOG_PATH", self.log_path)
        self.log_patch.start()

    def tearDown(self):
        self.log_patch.stop()
        self.tmpdir.cleanup()

    def decision(self, command: str) -> str | None:
        result = pre_tool_use.evaluate(bash_payload(command))
        return result.get("hookSpecificOutput", {}).get("permissionDecision")

    def assertBlocked(self, command: str, rule: str):
        result = pre_tool_use.evaluate(bash_payload(command))
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn(rule, result["hookSpecificOutput"]["permissionDecisionReason"])
        entries = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(entries), 1)
        entry = json.loads(entries[0])
        self.assertEqual(entry["command"], command)
        self.assertEqual(entry["project_path"], "/workspace/example")
        self.assertEqual(entry["rule"], rule)

    def assertAllowed(self, command: str):
        self.assertIsNone(self.decision(command))
        self.assertFalse(self.log_path.exists())

    def test_blocks_rm_rf_forms(self):
        for command in ("rm -rf build", "rm -fr build", "echo ok; rm -Rf /tmp/x"):
            with self.subTest(command=command):
                self.assertBlocked(command, "rm-rf")
                self.log_path.unlink()

    def test_blocks_sql_destructive_statements(self):
        cases = (
            ("psql -c 'DROP TABLE users'", "drop-table"),
            ("mysql -e 'DROP DATABASE app'", "drop-database"),
            ("psql -c 'TRUNCATE TABLE audit_log'", "truncate"),
            ("psql -c 'DELETE FROM users'", "delete-without-where"),
        )
        for command, rule in cases:
            with self.subTest(command=command):
                self.assertBlocked(command, rule)
                self.log_path.unlink()

    def test_allows_delete_with_where(self):
        self.assertAllowed("psql -c 'DELETE FROM users WHERE id = 1'")

    def test_blocks_force_push_variants(self):
        for command in ("git push --force origin main", "git push -f", "git push --force-with-lease"):
            with self.subTest(command=command):
                self.assertBlocked(command, "git-force-push")
                self.log_path.unlink()

    def test_allows_safe_bash_commands(self):
        for command in ("git push origin main", "rm -r build", "npm test", "sqlite3 app.db 'select * from users'"):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_non_bash_tool_is_ignored(self):
        result = pre_tool_use.evaluate({"tool_name": "Read", "tool_input": {"file_path": "README.md"}})
        self.assertTrue(result["continue"])
        self.assertFalse(self.log_path.exists())

    def test_project_path_falls_back_to_environment(self):
        payload = {"tool_name": "Bash", "tool_input": {"command": "rm -rf build"}}
        with patch.dict(os.environ, {"CLAUDE_PROJECT_DIR": "/env/project"}):
            pre_tool_use.evaluate(payload)
        entry = json.loads(self.log_path.read_text(encoding="utf-8"))
        self.assertEqual(entry["project_path"], "/env/project")

    def test_install_settings_is_idempotent(self):
        settings_path = Path(self.tmpdir.name) / "settings.json"
        pre_tool_use.install_settings(settings_path)
        pre_tool_use.install_settings(settings_path)
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        entries = settings["hooks"]["PreToolUse"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["matcher"], "Bash")


if __name__ == "__main__":
    unittest.main()
