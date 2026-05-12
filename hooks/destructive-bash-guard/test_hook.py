#!/usr/bin/env python3
"""Unit tests for pre_tool_use.py hook — validates all blocked patterns and pass-through."""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# Add parent dir to path so we can import the hook
sys.path.insert(0, os.path.dirname(__file__))
from pre_tool_use import check_command, log_blocked


class TestBlockedPatterns(unittest.TestCase):
    """Test that all required destructive patterns are blocked."""

    # --- rm -rf ---
    def test_rm_rf(self):
        reasons = check_command("rm -rf /tmp/old-project")
        self.assertTrue(any("rm" in r for r in reasons))

    def test_rm_force_recursive(self):
        reasons = check_command("rm -r -f node_modules")
        self.assertTrue(any("rm" in r for r in reasons))

    def test_rm_no_preserve_root(self):
        reasons = check_command("rm --no-preserve-root -rf /")
        self.assertTrue(any("no-preserve-root" in r for r in reasons))

    # --- DROP TABLE ---
    def test_drop_table(self):
        reasons = check_command('psql -c "DROP TABLE users"')
        self.assertTrue(any("DROP" in r for r in reasons))

    def test_drop_database(self):
        reasons = check_command('mysql -e "DROP DATABASE production"')
        self.assertTrue(any("DROP" in r for r in reasons))

    # --- TRUNCATE ---
    def test_truncate(self):
        reasons = check_command('psql -c "TRUNCATE TABLE logs"')
        self.assertTrue(any("TRUNCATE" in r for r in reasons))

    def test_truncate_no_table_keyword(self):
        reasons = check_command('sqlite3 db.sqlite "TRUNCATE sessions"')
        self.assertTrue(any("TRUNCATE" in r for r in reasons))

    # --- DELETE FROM without WHERE ---
    def test_delete_from_no_where(self):
        reasons = check_command('mysql -e "DELETE FROM logs"')
        self.assertTrue(any("DELETE FROM" in r for r in reasons))

    def test_delete_from_with_where_allowed(self):
        reasons = check_command('mysql -e "DELETE FROM logs WHERE id < 100"')
        self.assertEqual(len(reasons), 0)

    # --- git push --force ---
    def test_git_push_force(self):
        reasons = check_command("git push origin main --force")
        self.assertTrue(any("force" in r.lower() for r in reasons))

    def test_git_push_f(self):
        reasons = check_command("git push -f origin main")
        self.assertTrue(any("force" in r.lower() or "-f" in r for r in reasons))


class TestSafeCommands(unittest.TestCase):
    """Test that normal commands pass through without blocking."""

    def test_ls(self):
        reasons = check_command("ls -la")
        self.assertEqual(len(reasons), 0)

    def test_git_push_normal(self):
        reasons = check_command("git push origin main")
        self.assertEqual(len(reasons), 0)

    def test_rm_single_file(self):
        reasons = check_command("rm temp.txt")
        self.assertEqual(len(reasons), 0)

    def test_pip_install(self):
        reasons = check_command("pip install requests")
        self.assertEqual(len(reasons), 0)

    def test_git_commit(self):
        reasons = check_command("git commit -m 'fix bug'")
        self.assertEqual(len(reasons), 0)

    def test_mkdir(self):
        reasons = check_command("mkdir -p src/components")
        self.assertEqual(len(reasons), 0)

    def test_delete_from_with_where_complex(self):
        reasons = check_command("DELETE FROM users WHERE active = false AND last_login < '2024-01-01'")
        self.assertEqual(len(reasons), 0)

    def test_curl(self):
        reasons = check_command("curl -s https://api.example.com/data")
        self.assertEqual(len(reasons), 0)


class TestLogging(unittest.TestCase):
    """Test that blocked attempts are logged correctly."""

    def test_log_creates_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "blocked.log")
            with patch("pre_tool_use.LOG_FILE", log_file), \
                 patch("pre_tool_use.LOG_DIR", tmpdir):
                log_blocked("rm -rf /", "rm with -f flag", "/project")
                self.assertTrue(os.path.exists(log_file))
                with open(log_file) as f:
                    content = f.read()
                self.assertIn("rm -rf /", content)
                self.assertIn("rm with -f flag", content)
                self.assertIn("/project", content)

    def test_log_appends(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "blocked.log")
            with patch("pre_tool_use.LOG_FILE", log_file), \
                 patch("pre_tool_use.LOG_DIR", tmpdir):
                log_blocked("rm -rf /", "reason1", "/project1")
                log_blocked("DROP TABLE x", "reason2", "/project2")
                with open(log_file) as f:
                    lines = f.readlines()
                self.assertEqual(len(lines), 2)


class TestHookIntegration(unittest.TestCase):
    """Test the full stdin→stdout pipeline."""

    def _run_hook(self, tool_name: str, command: str) -> tuple[dict, int]:
        """Run the hook with mocked stdin, capture stdout and exit code."""
        input_data = {
            "hook_event_name": "PreToolUse",
            "session_id": "test-session",
            "cwd": "/test/project",
            "tool_name": tool_name,
            "tool_input": {"command": command},
        }
        stdin_json = json.dumps(input_data)

        with patch("sys.stdin", new_callable=lambda: type("S", (), {"read": lambda self: stdin_json})):
            import importlib
            import pre_tool_use
            importlib.reload(pre_tool_use)

            stdout_capture = []
            exit_code = 0

            with patch("sys.stdout") as mock_stdout, \
                 patch("sys.stderr"):
                mock_stdout.write.side_effect = lambda s: stdout_capture.append(s)

                try:
                    pre_tool_use.main()
                except SystemExit as e:
                    exit_code = e.code

        return stdout_capture, exit_code

    def test_bash_rm_rf_blocked(self):
        """rm -rf should be blocked with exit code 2."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "pre_tool_use.py")],
            input=json.dumps({
                "hook_event_name": "PreToolUse",
                "session_id": "test",
                "cwd": "/test",
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf /tmp/test"},
            }),
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 2)
        output = json.loads(result.stdout)
        self.assertEqual(output["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("rm", output["hookSpecificOutput"]["permissionDecisionReason"].lower())

    def test_bash_safe_command_passes(self):
        """Safe commands should pass with exit code 0."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "pre_tool_use.py")],
            input=json.dumps({
                "hook_event_name": "PreToolUse",
                "session_id": "test",
                "cwd": "/test",
                "tool_name": "Bash",
                "tool_input": {"command": "ls -la"},
            }),
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_non_bash_tool_passes(self):
        """Non-Bash tool calls should pass through."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "pre_tool_use.py")],
            input=json.dumps({
                "hook_event_name": "PreToolUse",
                "session_id": "test",
                "cwd": "/test",
                "tool_name": "Write",
                "tool_input": {"file_path": "test.txt", "content": "hello"},
            }),
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_empty_input_passes(self):
        """Empty stdin should not crash, just pass through."""
        import subprocess
        result = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(__file__), "pre_tool_use.py")],
            input="",
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
