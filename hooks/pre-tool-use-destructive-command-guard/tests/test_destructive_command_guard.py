from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / ".claude" / "hooks" / "destructive_command_guard.py"

spec = importlib.util.spec_from_file_location("destructive_command_guard", HOOK)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DetectionTests(unittest.TestCase):
    def assert_blocks(self, command: str, expected: str) -> None:
        reason = guard.find_violation(command)
        self.assertIsNotNone(reason)
        self.assertIn(expected, reason)

    def test_allows_normal_commands(self) -> None:
        self.assertIsNone(guard.find_violation("ls -la && git status --short"))

    def test_blocks_rm_recursive_force_variants(self) -> None:
        self.assert_blocks("rm -rf dist", "Recursive force delete")
        self.assert_blocks("rm -fr dist", "Recursive force delete")
        self.assert_blocks("sudo rm -Rf /tmp/example", "Recursive force delete")
        self.assert_blocks("rm --recursive --force dist", "Recursive force delete")

    def test_allows_non_recursive_or_non_force_rm(self) -> None:
        self.assertIsNone(guard.find_violation("rm -r dist"))
        self.assertIsNone(guard.find_violation("rm -f dist/output.log"))

    def test_blocks_git_force_push_variants(self) -> None:
        self.assert_blocks("git push --force origin main", "Git force push")
        self.assert_blocks("git push -f origin main", "Git force push")
        self.assert_blocks("git push --force-with-lease origin main", "Git force push")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocks("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocks("sqlite3 app.db 'TRUNCATE sessions'", "TRUNCATE")
        self.assert_blocks("sqlite3 app.db 'DELETE FROM users'", "DELETE FROM without WHERE")

    def test_allows_delete_with_where(self) -> None:
        self.assertIsNone(guard.find_violation("sqlite3 app.db 'DELETE FROM users WHERE id = 1'"))


class HookIOTests(unittest.TestCase):
    def run_hook(
        self,
        command: str,
        home: Path,
        *,
        cwd: str | None = "/tmp/project",
        project_dir: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        payload_data = {"tool_name": "Bash", "tool_input": {"command": command}}
        if cwd is not None:
            payload_data["cwd"] = cwd
        payload = json.dumps(payload_data)
        env = os.environ.copy()
        env["HOME"] = str(home)
        if project_dir is not None:
            env["CLAUDE_PROJECT_DIR"] = project_dir
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=payload,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def test_safe_command_is_silent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            result = self.run_hook("git status --short", Path(temp_home))
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((Path(temp_home) / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocked_command_emits_deny_json_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            result = self.run_hook("git push --force origin main", Path(temp_home))
            self.assertEqual(result.returncode, 0)
            data = json.loads(result.stdout)
            output = data["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("Git force push", output["permissionDecisionReason"])

            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            entry = json.loads(log_file.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["attempted_command"], "git push --force origin main")
            self.assertEqual(entry["project_path"], "/tmp/project")
            self.assertIn("Git force push", entry["reason"])

    def test_log_uses_claude_project_dir_when_payload_has_no_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_home:
            result = self.run_hook("DROP TABLE users", Path(temp_home), cwd=None, project_dir="/repo/from-env")
            self.assertEqual(result.returncode, 0)

            log_file = Path(temp_home) / ".claude" / "hooks" / "blocked.log"
            entry = json.loads(log_file.read_text(encoding="utf-8").strip())
            self.assertEqual(entry["project_path"], "/repo/from-env")


if __name__ == "__main__":
    unittest.main()
