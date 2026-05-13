from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = REPO_ROOT / "hooks" / "destructive_bash_guard" / "destructive_bash_guard.py"

spec = importlib.util.spec_from_file_location("destructive_bash_guard", HOOK_PATH)
guard = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(guard)


class DestructiveBashGuardTest(unittest.TestCase):
    def assert_blocked(self, command: str, rule: str) -> None:
        with self.assertRaises(guard.BlockedCommand) as context:
            guard.inspect_command(command)
        self.assertEqual(context.exception.rule, rule)

    def assert_allowed(self, command: str) -> None:
        guard.inspect_command(command)

    def test_blocks_recursive_forced_rm_variants(self) -> None:
        for command in [
            "rm -rf build",
            "rm -fr build",
            "sudo rm -Rf /tmp/app",
            "env FOO=bar rm --recursive --force cache",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command, "rm-recursive-force")

    def test_allows_non_forced_or_non_recursive_rm(self) -> None:
        for command in ["rm file.txt", "rm -r build", "rm -f file.txt"]:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_blocks_force_push_but_allows_force_with_lease(self) -> None:
        self.assert_blocked("git push --force origin main", "git-push-force")
        self.assert_blocked("git push -f origin main", "git-push-force")
        self.assert_allowed("git push --force-with-lease origin main")

    def test_blocks_destructive_sql(self) -> None:
        self.assert_blocked("DROP TABLE users", "drop-table")
        self.assert_blocked('psql -c "DROP TABLE users"', "drop-table")
        self.assert_blocked('mysql -e "TRUNCATE TABLE audit_log"', "truncate")
        self.assert_blocked('sqlite3 app.db "DELETE FROM sessions;"', "delete-without-where")

    def test_allows_delete_with_where(self) -> None:
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 42;"')
        self.assert_allowed('echo "DROP TABLE users"')

    def test_hook_returns_deny_json_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            hook_input = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "cwd": "/tmp/project",
                "tool_input": {"command": "rm -rf build"},
            }
            result = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(hook_input),
                text=True,
                capture_output=True,
                env={"HOME": home},
                check=False,
            )

            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            output = payload["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn("recursive and force", output["permissionDecisionReason"])

            log_path = Path(home) / ".claude" / "hooks" / "blocked.log"
            log_entry = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(log_entry["attempted_command"], "rm -rf build")
            self.assertEqual(log_entry["project_path"], "/tmp/project")
            self.assertEqual(log_entry["rule"], "rm-recursive-force")


if __name__ == "__main__":
    unittest.main()
