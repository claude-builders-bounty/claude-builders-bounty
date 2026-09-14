#!/usr/bin/env python3
"""
Automated validation suite for Claude Code Pre-Tool-Use Destructive Command Hook.
Verifies official Claude Code PreToolUse blocking protocol and safe 2-command installer.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from block_destructive_bash import is_destructive_command, log_blocked_attempt, install_hook


class TestDestructiveCommandHook(unittest.TestCase):
    """Test suite verifying all acceptance criteria, official Claude Code protocol, and installer."""

    def setUp(self) -> None:
        self.hook_path = os.path.join(os.path.dirname(__file__), "block_destructive_bash.py")
        self.temp_dir = tempfile.mkdtemp(prefix="claude_hook_test_")

    def tearDown(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_hook_with_json(self, tool_input_command: str) -> subprocess.CompletedProcess:
        """Run hook with standard Claude Code PreToolUse JSON payload on stdin."""
        payload = json.dumps({
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": tool_input_command
            },
            "cwd": "/projects/test-saas"
        })
        return subprocess.run(
            [sys.executable, self.hook_path],
            input=payload,
            capture_output=True,
            text=True,
        )

    # 1. rm -rf -> actual Claude blocking signal
    def test_01_rm_rf_blocked(self) -> None:
        variants = [
            "rm -rf /tmp/data",
            "rm -fr build/",
            "rm -r -f node_modules",
            "rm -f -r dist",
            "rm --recursive --force cache",
            "rm -rf ./logs && npm start",
        ]
        for cmd in variants:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0, f"Expected exit 0 with JSON denial for {cmd!r}")
            out_data = json.loads(proc.stdout)
            hook_out = out_data.get("hookSpecificOutput", {})
            self.assertEqual(hook_out.get("hookEventName"), "PreToolUse")
            self.assertEqual(hook_out.get("permissionDecision"), "deny")
            self.assertTrue(len(hook_out.get("permissionDecisionReason", "")) > 0)
            self.assertIn("rm -rf", hook_out.get("permissionDecisionReason"))

    # 2. DROP TABLE -> actual Claude blocking signal
    def test_02_drop_table_blocked(self) -> None:
        variants = [
            "DROP TABLE users;",
            "drop table if exists accounts",
            "sqlite3 dev.db 'DROP TABLE audit_logs;'",
            "psql -d app -c 'DROP TABLE sessions'",
        ]
        for cmd in variants:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0)
            out_data = json.loads(proc.stdout)
            hook_out = out_data.get("hookSpecificOutput", {})
            self.assertEqual(hook_out.get("hookEventName"), "PreToolUse")
            self.assertEqual(hook_out.get("permissionDecision"), "deny")
            self.assertTrue(len(hook_out.get("permissionDecisionReason", "")) > 0)
            self.assertIn("DROP TABLE", hook_out.get("permissionDecisionReason"))

    # 3. git push --force -> actual Claude blocking signal
    def test_03_git_push_force_blocked(self) -> None:
        variants = [
            "git push origin main --force",
            "git push -f",
            "git push origin feature --force-with-lease",
            "git push --force-if-includes",
        ]
        for cmd in variants:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0)
            out_data = json.loads(proc.stdout)
            hook_out = out_data.get("hookSpecificOutput", {})
            self.assertEqual(hook_out.get("hookEventName"), "PreToolUse")
            self.assertEqual(hook_out.get("permissionDecision"), "deny")
            self.assertTrue(len(hook_out.get("permissionDecisionReason", "")) > 0)
            self.assertIn("git push --force", hook_out.get("permissionDecisionReason"))

    # 4. TRUNCATE -> actual Claude blocking signal
    def test_04_truncate_blocked(self) -> None:
        variants = [
            "TRUNCATE TABLE users;",
            "truncate audit_events",
            "TRUNCATE `orders`",
        ]
        for cmd in variants:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0)
            out_data = json.loads(proc.stdout)
            hook_out = out_data.get("hookSpecificOutput", {})
            self.assertEqual(hook_out.get("hookEventName"), "PreToolUse")
            self.assertEqual(hook_out.get("permissionDecision"), "deny")
            self.assertTrue(len(hook_out.get("permissionDecisionReason", "")) > 0)
            self.assertIn("TRUNCATE", hook_out.get("permissionDecisionReason"))

    # 5. DELETE FROM without WHERE -> actual Claude blocking signal
    def test_05_delete_from_without_where_blocked(self) -> None:
        variants = [
            "DELETE FROM users;",
            "delete from accounts",
            "sqlite3 app.db 'DELETE FROM sessions;'",
        ]
        for cmd in variants:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0)
            out_data = json.loads(proc.stdout)
            hook_out = out_data.get("hookSpecificOutput", {})
            self.assertEqual(hook_out.get("hookEventName"), "PreToolUse")
            self.assertEqual(hook_out.get("permissionDecision"), "deny")
            self.assertTrue(len(hook_out.get("permissionDecisionReason", "")) > 0)
            self.assertIn("DELETE FROM", hook_out.get("permissionDecisionReason"))

    # 6. Specific regression test: EXIT CODE 1 IS NOT USED FOR BLOCKING
    def test_06_exit_code_1_not_used_for_blocking(self) -> None:
        proc = self._run_hook_with_json("rm -rf /test")
        self.assertNotEqual(proc.returncode, 1, "Exit code 1 is a non-blocking error in Claude Code and must not be used for denial")
        self.assertEqual(proc.returncode, 0, "Official Claude Code protocol uses exit 0 with structured deny JSON on stdout")
        out_data = json.loads(proc.stdout)
        self.assertEqual(out_data.get("hookSpecificOutput", {}).get("permissionDecision"), "deny")

    # 7. Safe commands allowed without deny decision
    def test_07_safe_commands_allowed(self) -> None:
        safe_cmds = [
            "ls -la",
            "git status",
            "git push origin main",
            "git push origin feature-branch",
            "rm file.txt",
            "rm -f single_file.log",
            "rm -r empty_dir",
            "DELETE FROM users WHERE id = 123;",
            "delete from sessions where expired_at < now();",
            "echo 'DROP TABLE is dangerous'",
            "echo 'rm -rf /' > warning.txt",
            "npm test",
            "npm run build",
            "python script.py",
        ]
        for cmd in safe_cmds:
            proc = self._run_hook_with_json(cmd)
            self.assertEqual(proc.returncode, 0, f"Expected exit 0 for safe command {cmd!r}")
            if proc.stdout.strip():
                try:
                    out_data = json.loads(proc.stdout)
                    decision = out_data.get("hookSpecificOutput", {}).get("permissionDecision")
                    self.assertNotEqual(decision, "deny", f"Safe command {cmd!r} was falsely denied")
                except json.JSONDecodeError:
                    pass

    # 8. Logging format verification
    def test_08_logging_format(self) -> None:
        temp_log = os.path.join(self.temp_dir, "blocked.log")
        log_blocked_attempt(
            command="rm -rf /test",
            project_path="/projects/my-saas",
            reason="Test destructive rule",
            log_file_override=temp_log,
        )
        self.assertTrue(os.path.exists(temp_log))
        with open(temp_log, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("BLOCKED", content)
        self.assertIn("Command:      rm -rf /test", content)
        self.assertIn("Project Path: /projects/my-saas", content)
        self.assertIn("Reason:       Test destructive rule", content)

    # 9. Installer creates settings.json when none exists
    def test_09_installer_fresh_creation(self) -> None:
        claude_dir = os.path.join(self.temp_dir, ".claude")
        res = install_hook(claude_dir_override=claude_dir)
        self.assertEqual(res, 0)

        settings_path = os.path.join(claude_dir, "settings.json")
        self.assertTrue(os.path.exists(settings_path))

        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pre_tool_use = data.get("hooks", {}).get("PreToolUse", [])
        self.assertEqual(len(pre_tool_use), 1)
        self.assertEqual(pre_tool_use[0].get("matcher"), "Bash")
        self.assertIn("pre-tool-use.py", pre_tool_use[0].get("command", ""))

    # 10. Installer preserves existing settings and other hooks
    def test_10_installer_preserves_existing_settings(self) -> None:
        claude_dir = os.path.join(self.temp_dir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        settings_path = os.path.join(claude_dir, "settings.json")

        initial_config = {
            "theme": "dark",
            "autoUpdaterStatus": "disabled",
            "hooks": {
                "PreToolUse": [
                    {"matcher": "Read", "command": "python3 ~/.claude/hooks/check_read.py"}
                ],
                "PostToolUse": [
                    {"matcher": "Bash", "command": "python3 ~/.claude/hooks/log_post.py"}
                ]
            }
        }
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(initial_config, f, indent=2)

        res = install_hook(claude_dir_override=claude_dir)
        self.assertEqual(res, 0)

        with open(settings_path, "r", encoding="utf-8") as f:
            updated = json.load(f)

        # Unrelated settings preserved
        self.assertEqual(updated.get("theme"), "dark")
        self.assertEqual(updated.get("autoUpdaterStatus"), "disabled")

        # Unrelated hooks preserved
        self.assertEqual(len(updated["hooks"]["PostToolUse"]), 1)
        self.assertEqual(len(updated["hooks"]["PreToolUse"]), 2)

        # New hook present
        matchers = [h.get("matcher") for h in updated["hooks"]["PreToolUse"]]
        self.assertIn("Read", matchers)
        self.assertIn("Bash", matchers)

    # 11. Installer is idempotent (no duplicate registration)
    def test_11_installer_idempotency(self) -> None:
        claude_dir = os.path.join(self.temp_dir, ".claude")
        # Run 3 times
        for _ in range(3):
            res = install_hook(claude_dir_override=claude_dir)
            self.assertEqual(res, 0)

        settings_path = os.path.join(claude_dir, "settings.json")
        with open(settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pre_tool_use = data.get("hooks", {}).get("PreToolUse", [])
        self.assertEqual(len(pre_tool_use), 1, "Idempotent install must not duplicate hook registration")

    # 12. Installer fails closed on malformed existing settings.json
    def test_12_installer_fails_closed_on_malformed_json(self) -> None:
        claude_dir = os.path.join(self.temp_dir, ".claude")
        os.makedirs(claude_dir, exist_ok=True)
        settings_path = os.path.join(claude_dir, "settings.json")

        malformed_content = "{ this is not valid json; broken content !!!"
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(malformed_content)

        res = install_hook(claude_dir_override=claude_dir)
        self.assertEqual(res, 1, "Installer must return error on malformed JSON")

        with open(settings_path, "r", encoding="utf-8") as f:
            content_after = f.read()

        self.assertEqual(content_after, malformed_content, "Malformed settings must not be overwritten or wiped")

    # 13. Installer CLI --install via subprocess with isolated env
    def test_13_installer_cli_invocation(self) -> None:
        env = os.environ.copy()
        env["CLAUDE_HOME_OVERRIDE"] = self.temp_dir

        proc = subprocess.run(
            [sys.executable, self.hook_path, "--install"],
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertIn("[SUCCESS]", proc.stdout)

        settings_path = os.path.join(self.temp_dir, ".claude", "settings.json")
        self.assertTrue(os.path.exists(settings_path))


if __name__ == "__main__":
    unittest.main()
