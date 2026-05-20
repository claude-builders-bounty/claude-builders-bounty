#!/usr/bin/env python3
"""Regression tests for block_destructive.py."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "block_destructive.py"
INSTALLER = ROOT / "install.py"


def run_hook(command: str, tool_name: str = "Bash") -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": tool_name,
        "tool_input": {"command": command},
        "cwd": "/tmp/example-project",
        "project_path": "/tmp/example-project",
    }
    env = os.environ.copy()
    temp_home = tempfile.TemporaryDirectory()
    env["HOME"] = temp_home.name
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    result.temp_home = temp_home  # type: ignore[attr-defined]
    return result


class DestructiveCommandHookTest(unittest.TestCase):
    def assert_blocked(self, command: str, expected_rule: str) -> None:
        result = run_hook(command)
        self.addCleanup(result.temp_home.cleanup)  # type: ignore[attr-defined]
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        output = response["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn(expected_rule, output["permissionDecisionReason"])

        log_path = Path(result.temp_home.name) / ".claude" / "hooks" / "blocked.log"  # type: ignore[attr-defined]
        record = json.loads(log_path.read_text(encoding="utf-8").strip())
        self.assertEqual(record["command"], command)
        self.assertEqual(record["project_path"], "/tmp/example-project")
        self.assertEqual(record["rule"], expected_rule)
        self.assertIn("timestamp", record)

    def assert_allowed(self, command: str, tool_name: str = "Bash") -> None:
        result = run_hook(command, tool_name=tool_name)
        self.addCleanup(result.temp_home.cleanup)  # type: ignore[attr-defined]
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        log_path = Path(result.temp_home.name) / ".claude" / "hooks" / "blocked.log"  # type: ignore[attr-defined]
        self.assertFalse(log_path.exists())

    def test_blocks_rm_rf_variants(self) -> None:
        self.assert_blocked("rm -rf build", "rm -rf")
        self.assert_blocked("rm -fr ./dist", "rm -rf")
        self.assert_blocked("/bin/rm -Rf ./dist", "rm -rf")
        self.assert_blocked("npm test && rm -rf build", "rm -rf")

    def test_blocks_drop_table_and_truncate(self) -> None:
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE")

    def test_blocks_git_force_push(self) -> None:
        self.assert_blocked("git push origin main --force", "git push --force")
        self.assert_blocked("git push --force-with-lease", "git push --force")

    def test_blocks_delete_without_where(self) -> None:
        self.assert_blocked("sqlite3 app.db 'DELETE FROM users;'", "DELETE FROM without WHERE")
        self.assert_blocked("psql -c 'delete from sessions'", "DELETE FROM without WHERE")
        self.assert_blocked("echo ready; psql -c 'DROP TABLE users'", "DROP TABLE")

    def test_allows_normal_commands(self) -> None:
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin feature")
        self.assert_allowed("sqlite3 app.db 'DELETE FROM users WHERE id = 1;'")
        self.assert_allowed("echo 'DROP TABLE appears in docs only'")
        self.assert_allowed("rm -rf ignored-for-non-bash-tools", tool_name="Write")

    def test_installer_copies_hook_and_updates_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            env = os.environ.copy()
            env["HOME"] = temp_home
            result = subprocess.run(
                [sys.executable, str(INSTALLER)],
                text=True,
                capture_output=True,
                env=env,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            installed_hook = Path(temp_home) / ".claude" / "hooks" / "block_destructive.py"
            self.assertTrue(installed_hook.exists())
            self.assertTrue(os.access(installed_hook, os.X_OK))

            settings_path = Path(temp_home) / ".claude" / "settings.json"
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            entries = settings["hooks"]["PreToolUse"]
            self.assertEqual(entries[0]["matcher"], "Bash")
            self.assertEqual(entries[0]["hooks"][0]["type"], "command")


if __name__ == "__main__":
    unittest.main()
