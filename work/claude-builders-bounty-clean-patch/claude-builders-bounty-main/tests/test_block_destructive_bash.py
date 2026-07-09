import importlib.util
import json
import subprocess
import sys
import os
import tempfile
import unittest
from pathlib import Path

HOOK_PATH = Path(__file__).resolve().parents[1] / "hooks" / "block-destructive-bash" / "block_destructive_bash.py"
spec = importlib.util.spec_from_file_location("block_destructive_bash", HOOK_PATH)
hook = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = hook
spec.loader.exec_module(hook)


class DestructiveBashHookTests(unittest.TestCase):
    def assert_blocked(self, command, pattern):
        match = hook.find_blocked_pattern(command)
        self.assertIsNotNone(match, command)
        self.assertEqual(match.pattern, pattern)

    def assert_allowed(self, command):
        self.assertIsNone(hook.find_blocked_pattern(command), command)

    def test_blocks_required_patterns(self):
        self.assert_blocked("rm -rf dist", "rm -rf")
        self.assert_blocked("sudo rm -fr /tmp/demo", "rm -rf")
        self.assert_blocked("git push --force origin main", "git push --force")
        self.assert_blocked("psql -c 'DROP TABLE users'", "DROP TABLE")
        self.assert_blocked("mysql -e 'TRUNCATE audit_log'", "TRUNCATE")
        self.assert_blocked("psql -c 'DELETE FROM sessions'", "DELETE FROM without WHERE")

    def test_allows_normal_commands(self):
        self.assert_allowed("npm test")
        self.assert_allowed("git push origin feature/safe")
        self.assert_allowed("rm build.log")
        self.assert_allowed("psql -c 'DELETE FROM sessions WHERE expires_at < now()'")
        self.assert_allowed("python3 scripts/report.py")

    def test_denial_payload_uses_claude_code_pre_tool_schema(self):
        match = hook.BlockMatch("rm -rf", "test reason")
        payload = hook.denial_payload(match)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("rm -rf", payload["hookSpecificOutput"]["permissionDecisionReason"])

    def test_log_contains_timestamp_command_and_project_path(self):
        temp_root = Path(__file__).resolve().parents[1] / ".test-tmp"
        temp_root.mkdir(exist_ok=True)
        log_path = temp_root / "blocked.log"
        if log_path.exists():
            log_path.unlink()
        match = hook.BlockMatch("DROP TABLE", "test reason")
        hook.append_block_log("DROP TABLE users", "/tmp/project", match, log_path)
        entry = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["attempted_command"], "DROP TABLE users")
        self.assertEqual(entry["project_path"], "/tmp/project")

    def test_hook_process_blocks_bash_and_stays_silent_for_safe_commands(self):
        env = os.environ.copy()
        env["CLAUDE_BLOCKED_LOG"] = str(Path(__file__).resolve().parents[1] / ".test-tmp" / "subprocess-blocked.log")
        blocked = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git push --force", "cwd": "/repo"}}),
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        self.assertIn('"permissionDecision": "deny"', blocked.stdout)

        safe = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status", "cwd": "/repo"}}),
            text=True,
            capture_output=True,
            check=True,
            env=env,
        )
        self.assertEqual(safe.stdout, "")


if __name__ == "__main__":
    unittest.main()