import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "hooks" / "pre-tool-use" / "block_destructive_bash.py"

sys.path.insert(0, str(HOOK_SCRIPT.parent))
from block_destructive_bash import check_command_safety

class TestClaudePreToolHook(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_path = Path(self.temp_dir.name) / "blocked.log"
        self.env = os.environ.copy()
        self.env["CLAUDE_HOOK_LOG_PATH"] = str(self.log_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def run_hook_with_json(self, payload: dict) -> tuple[int, str, str]:
        proc = subprocess.run(
            [sys.executable, str(HOOK_SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=self.env,
        )
        return proc.returncode, proc.stdout, proc.stderr

    def test_blocks_rm_rf_variants(self):
        dangerous_rms = [
            "rm -rf /",
            "rm -fr /home/user",
            "rm -r -f /var/data",
            "rm --recursive --force .",
        ]
        for cmd in dangerous_rms:
            is_blocked, reason = check_command_safety(cmd)
            self.assertTrue(is_blocked, f"Expected {cmd} to be blocked")
            code, out, err = self.run_hook_with_json({"tool": "Bash", "command": cmd})
            self.assertEqual(code, 1, f"Expected non-zero exit for: {cmd}")
            self.assertIn("BLOCKED", err)

    def test_blocks_drop_table(self):
        cmd = "psql -d prod -c 'DROP TABLE users;'"
        is_blocked, reason = check_command_safety(cmd)
        self.assertTrue(is_blocked)
        code, out, err = self.run_hook_with_json({"tool": "Bash", "command": cmd})
        self.assertEqual(code, 1)

    def test_blocks_git_push_force(self):
        for cmd in ["git push origin main --force", "git push -f", "git push origin --force-with-lease"]:
            is_blocked, reason = check_command_safety(cmd)
            self.assertTrue(is_blocked, f"Expected {cmd} to be blocked")
            code, out, err = self.run_hook_with_json({"tool": "Bash", "command": cmd})
            self.assertEqual(code, 1)

    def test_blocks_truncate(self):
        cmd = "mysql -e 'TRUNCATE TABLE logs'"
        is_blocked, reason = check_command_safety(cmd)
        self.assertTrue(is_blocked)

    def test_blocks_delete_without_where_only(self):
        safe_delete = "DELETE FROM items WHERE id = 42"
        is_blocked, _ = check_command_safety(safe_delete)
        self.assertFalse(is_blocked)

        unsafe_delete = "DELETE FROM items;"
        is_blocked, _ = check_command_safety(unsafe_delete)
        self.assertTrue(is_blocked)

    def test_allows_safe_commands(self):
        safe_cmds = [
            "git status",
            "npm test",
            "pytest",
            "ls -la",
            "cat README.md",
            "python -m build",
        ]
        for cmd in safe_cmds:
            is_blocked, reason = check_command_safety(cmd)
            self.assertFalse(is_blocked, f"Safe command was falsely blocked: {cmd}")
            code, out, err = self.run_hook_with_json({"tool": "Bash", "command": cmd})
            self.assertEqual(code, 0, f"Expected 0 exit for safe command: {cmd}")

    def test_logs_blocked_attempt_to_audit_file(self):
        cmd = "rm -rf /tmp/scratch"
        code, out, err = self.run_hook_with_json({"tool": "Bash", "command": cmd})
        self.assertEqual(code, 1)
        self.assertTrue(self.log_path.exists())
        log_content = self.log_path.read_text(encoding="utf-8")
        self.assertIn("REASON:", log_content)
        self.assertIn(cmd, log_content)

if __name__ == "__main__":
    unittest.main()
