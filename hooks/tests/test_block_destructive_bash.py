from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


HOOK_PATH = Path(__file__).resolve().parents[1] / "block_destructive_bash.py"
SPEC = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(hook)


class DestructiveCommandDetectionTests(unittest.TestCase):
    def test_blocks_rm_rf_variants(self) -> None:
        for command in ("rm -rf build", "rm -fr build", "rm -r -f build", "rm --recursive --force build"):
            self.assertIn("rm -rf", hook.blocked_reason(command))

    def test_blocks_sql_destructive_commands(self) -> None:
        self.assertIn("DROP TABLE", hook.blocked_reason("psql -c 'DROP TABLE users'"))
        self.assertIn("TRUNCATE", hook.blocked_reason("mysql -e 'truncate sessions'"))
        self.assertIn("DELETE FROM", hook.blocked_reason("psql -c 'DELETE FROM users;'"))

    def test_allows_delete_with_where(self) -> None:
        self.assertIsNone(hook.blocked_reason("psql -c 'DELETE FROM users WHERE id = 1;'"))

    def test_blocks_git_force_push(self) -> None:
        self.assertIn("history rewrites", hook.blocked_reason("git push --force origin main"))
        self.assertIn("history rewrites", hook.blocked_reason("git push -f origin main"))
        self.assertIn("history rewrites", hook.blocked_reason("git push --force-with-lease origin main"))

    def test_allows_normal_bash_commands(self) -> None:
        safe_commands = [
            "npm test",
            "git push origin main",
            "rm build/output.txt",
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "python scripts/build.py",
        ]
        for command in safe_commands:
            self.assertIsNone(hook.blocked_reason(command), command)


class HookMainTests(unittest.TestCase):
    def run_hook(self, payload: dict[str, object], log_path: Path) -> tuple[int, str]:
        stdin = io.StringIO(json.dumps(payload))
        stdout = io.StringIO()
        with patch.object(hook.sys, "stdin", stdin), patch.dict(os.environ, {"CLAUDE_HOOKS_BLOCKED_LOG": str(log_path)}):
            with redirect_stdout(stdout):
                code = hook.main()
        return code, stdout.getvalue()

    def test_blocked_command_denies_and_logs(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf build"},
            "cwd": "/tmp/project",
            "tool_use_id": "toolu_123",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "blocked.log"
            code, output = self.run_hook(payload, log_path)

            self.assertEqual(code, 0)
            decision = json.loads(output)
            self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("rm -rf", decision["hookSpecificOutput"]["permissionDecisionReason"])

            entries = log_path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(entries), 1)
            entry = json.loads(entries[0])
            self.assertEqual(entry["attempted_command"], "rm -rf build")
            self.assertEqual(entry["project_path"], "/tmp/project")

    def test_safe_command_is_silent(self) -> None:
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "npm test"},
            "cwd": "/tmp/project",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            code, output = self.run_hook(payload, Path(temp_dir) / "blocked.log")
            self.assertEqual(code, 0)
            self.assertEqual(output, "")


if __name__ == "__main__":
    unittest.main()
