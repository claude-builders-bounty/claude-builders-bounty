from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


HOOK_PATH = Path(__file__).resolve().parents[1] / "pre_tool_use.py"
SPEC = importlib.util.spec_from_file_location("pre_tool_use", HOOK_PATH)
pre_tool_use = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules["pre_tool_use"] = pre_tool_use
SPEC.loader.exec_module(pre_tool_use)


class DestructiveCommandGuardTest(unittest.TestCase):
    def assert_blocked(self, command: str, rule: str) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_path = Path(tmp_dir) / "blocked.log"
            with mock.patch.object(pre_tool_use, "LOG_PATH", log_path):
                response = pre_tool_use.handle({"tool_input": {"command": command}, "cwd": "/repo"})

            output = response["hookSpecificOutput"]
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn(rule, output["permissionDecisionReason"])
            log_entry = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(log_entry["command"], command)
            self.assertEqual(log_entry["project_path"], "/repo")
            self.assertEqual(log_entry["rule"], rule)

    def assert_allowed(self, command: str) -> None:
        response = pre_tool_use.handle({"tool_input": {"command": command}, "cwd": "/repo"})
        self.assertIsNone(response)

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("sudo rm -fr /tmp/demo", "rm -rf")

    def test_blocks_force_push_variants(self) -> None:
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("git push -f origin main", "git push --force")
        self.assert_blocked("git push --force-with-lease", "git push --force")

    def test_blocks_required_sql_patterns(self) -> None:
        self.assert_blocked('psql -c "DROP TABLE users"', "DROP TABLE")
        self.assert_blocked('mysql -e "TRUNCATE TABLE audit_log"', "TRUNCATE")
        self.assert_blocked('psql -c "DELETE FROM users;"', "DELETE FROM without WHERE")

    def test_allows_safe_commands(self) -> None:
        self.assert_allowed("git push origin main")
        self.assert_allowed("rm -r build")
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1;"')
        self.assert_allowed("python3 -m pytest")


if __name__ == "__main__":
    unittest.main()
