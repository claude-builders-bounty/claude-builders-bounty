import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HOOK_PATH = Path(__file__).with_name("safe_bash_guard.py")


spec = importlib.util.spec_from_file_location("safe_bash_guard", HOOK_PATH)
safe_bash_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safe_bash_guard)


def event(command):
    return {
        "session_id": "test",
        "transcript_path": "/tmp/transcript.jsonl",
        "cwd": "/tmp/project",
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


class SafeBashGuardTests(unittest.TestCase):
    def test_safe_command_is_allowed(self):
        self.assertIsNone(safe_bash_guard.find_block_reason("npm test"))

    def test_blocks_rm_rf(self):
        reason = safe_bash_guard.find_block_reason("rm -rf dist")
        self.assertEqual(reason[0], "recursive force deletion")

    def test_blocks_split_rm_flags(self):
        reason = safe_bash_guard.find_block_reason("sudo rm -r -f /tmp/build")
        self.assertEqual(reason[0], "recursive force deletion")

    def test_blocks_force_push(self):
        reason = safe_bash_guard.find_block_reason("git push origin main --force")
        self.assertEqual(reason[0], "force push")

    def test_blocks_drop_table(self):
        reason = safe_bash_guard.find_block_reason('psql -c "DROP TABLE users"')
        self.assertEqual(reason[0], "drop table")

    def test_blocks_truncate(self):
        reason = safe_bash_guard.find_block_reason('mysql -e "TRUNCATE TABLE sessions"')
        self.assertEqual(reason[0], "truncate")

    def test_blocks_delete_without_where(self):
        reason = safe_bash_guard.find_block_reason('psql -c "DELETE FROM users;"')
        self.assertEqual(reason[0], "delete without where")

    def test_allows_delete_with_where(self):
        reason = safe_bash_guard.find_block_reason('psql -c "DELETE FROM users WHERE id = 1;"')
        self.assertIsNone(reason)

    def test_hook_returns_deny_json_for_blocked_command(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env = dict(os.environ)
            env["CLAUDE_SAFE_BASH_GUARD_LOG"] = str(Path(tmpdir) / "blocked.log")
            proc = subprocess.run(
                [sys.executable, str(HOOK_PATH)],
                input=json.dumps(event("rm -rf dist")),
                text=True,
                capture_output=True,
                check=True,
                env=env,
            )
        output = json.loads(proc.stdout)
        decision = output["hookSpecificOutput"]["permissionDecision"]
        self.assertEqual(decision, "deny")

    def test_hook_outputs_nothing_for_safe_command(self):
        proc = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(event("npm test")),
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertEqual(proc.stdout, "")


if __name__ == "__main__":
    unittest.main()
