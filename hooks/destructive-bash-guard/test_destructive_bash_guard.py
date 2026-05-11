#!/usr/bin/env python3
"""Unit tests for Destructive Bash Guard."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch


MODULE_PATH = Path(__file__).with_name("destructive_bash_guard.py")
SPEC = importlib.util.spec_from_file_location("destructive_bash_guard", MODULE_PATH)
guard = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def payload(command: str) -> dict:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "cwd": "/tmp/example-project",
        "tool_input": {"command": command},
    }


class DetectionTests(TestCase):
    def assert_rule(self, command: str, rule: str) -> None:
        violation = guard.find_violation(command)
        self.assertIsNotNone(violation, command)
        self.assertEqual(violation.rule, rule)

    def assert_allowed(self, command: str) -> None:
        self.assertIsNone(guard.find_violation(command), command)

    def test_blocks_recursive_forced_rm_variants(self) -> None:
        for command in ("rm -rf build", "rm -fr build", "rm -R --force dist", "rm -r -f node_modules"):
            self.assert_rule(command, "rm_recursive_force")

    def test_blocks_force_push_variants(self) -> None:
        for command in ("git push --force", "git push -f origin main", "git -C repo push --force-with-lease"):
            self.assert_rule(command, "git_force_push")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_rule('psql -c "DROP TABLE users"', "drop_table")
        self.assert_rule("mysql -e 'TRUNCATE TABLE audit_log'", "truncate")
        self.assert_rule('psql -c "DELETE FROM users"', "delete_from_without_where")

    def test_allows_safe_commands(self) -> None:
        for command in (
            "rm build.log",
            "git push origin main",
            'psql -c "DELETE FROM users WHERE id = 1"',
            "python3 -m pytest",
            "echo 'DROP TABLE appears in docs only'",
        ):
            self.assert_allowed(command)


class HookBehaviorTests(TestCase):
    def test_allowed_command_is_silent(self) -> None:
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH)],
            input=json.dumps(payload("python3 -m pytest")),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def test_blocked_command_logs_and_denies(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "blocked.log"
            with patch.object(guard, "LOG_PATH", log_path):
                with patch("sys.stdout") as stdout:
                    code = guard.handle(payload("rm -rf build"))

            self.assertEqual(code, 0)
            response = json.loads("".join(call.args[0] for call in stdout.write.call_args_list if call.args))
            hook_output = response["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("recursive delete", hook_output["permissionDecisionReason"])
            log_text = log_path.read_text(encoding="utf-8")
            self.assertIn("project=/tmp/example-project", log_text)
            self.assertIn("rule=rm_recursive_force", log_text)
            self.assertIn("command=rm -rf build", log_text)


if __name__ == "__main__":
    main()
