import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

MODULE = Path(__file__).with_name("destructive_command_guard.py")
INSTALLER = Path(__file__).with_name("install_hook.py")
spec = importlib.util.spec_from_file_location("guard", MODULE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardUnitTests(unittest.TestCase):
    def assertBlocked(self, command):
        self.assertIsNotNone(guard.reason_for(command), command)

    def assertAllowed(self, command):
        self.assertIsNone(guard.reason_for(command), command)

    def test_required_patterns_and_common_variants_blocked(self):
        for command in [
            "rm -rf /tmp/demo",
            "rm -fr build",
            "rm -r -f build",
            "sudo rm -R -f /tmp/demo",
            "/bin/rm --recursive --force dist",
            "echo ok && rm -rf /tmp/demo",
            "echo `rm -rf /tmp/demo`",
            "if true; then rm -rf /tmp/demo; fi",
            "psql -c 'DROP TABLE users'",
            "sqlite3 app.db 'drop table sessions;'",
            "git push --force origin main",
            "git push --force-with-lease origin main",
            "sudo git push -f origin main",
            "TRUNCATE TABLE sessions",
            "mysql -e 'TRUNCATE sessions'",
            "DELETE FROM users;",
            "sqlite3 app.db 'delete from users'",
            "echo 'DELETE FROM users' | psql",
        ]:
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_delete_with_where_allowed(self):
        for command in [
            "DELETE FROM users WHERE id = 42;",
            "sqlite3 app.db 'DELETE FROM users WHERE id = 42;'",
            "psql -c 'delete from sessions where expired = true;'",
        ]:
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_where_in_comment_or_literal_does_not_bypass_guard(self):
        for command in [
            "DELETE FROM users /* WHERE id = 1 */;",
            "DELETE FROM users RETURNING 'WHERE';",
            'DELETE FROM users RETURNING "where";',
        ]:
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_normal_bash_and_harmless_mentions_are_allowed(self):
        for command in [
            "rm file.txt",
            "rm -r directory",
            "rm -f file.txt",
            "rm -- -rf",
            "git push origin main",
            "git status",
            "SELECT * FROM users",
            "echo 'DROP TABLE users'",
            "printf '%s\\n' 'git push --force'",
            "echo 'rm -rf /tmp/demo'",
        ]:
            with self.subTest(command=command):
                self.assertAllowed(command)


class HookIntegrationTests(unittest.TestCase):
    def run_hook(self, payload, home):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            [sys.executable, str(MODULE)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_blocked_command_denies_and_logs_all_required_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            payload = {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "sudo rm -rf /tmp/demo"},
                "cwd": "/work/project",
            }
            result = self.run_hook(payload, home)

            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            decision = output["hookSpecificOutput"]
            self.assertEqual(decision["hookEventName"], "PreToolUse")
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn(
                "recursive forced deletion",
                decision["permissionDecisionReason"],
            )

            log_path = home / ".claude" / "hooks" / "blocked.log"
            self.assertTrue(log_path.exists())
            log_line = log_path.read_text(encoding="utf-8")
            self.assertIn("/work/project", log_line)
            self.assertIn("sudo rm -rf /tmp/demo", log_line)
            self.assertRegex(log_line, r"^\d{4}-\d{2}-\d{2}T")

    def test_safe_bash_is_silent_and_not_logged(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            result = self.run_hook(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": "git status"},
                    "cwd": "/work/project",
                },
                home,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_non_bash_tool_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Read",
                    "tool_input": {"command": "rm -rf /"},
                    "cwd": "/work/project",
                },
                Path(tmp),
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")


class InstallerIntegrationTests(unittest.TestCase):
    def test_installer_is_one_command_preserves_settings_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            settings = home / ".claude" / "settings.json"
            settings.parent.mkdir(parents=True)
            settings.write_text(
                json.dumps(
                    {
                        "permissions": {"allow": ["Bash(git status)"]},
                        "hooks": {"PostToolUse": []},
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["HOME"] = str(home)

            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(INSTALLER)],
                    text=True,
                    capture_output=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            data = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(
                data["permissions"]["allow"],
                ["Bash(git status)"],
            )
            self.assertEqual(data["hooks"]["PostToolUse"], [])
            self.assertEqual(len(data["hooks"]["PreToolUse"]), 1)

            installed_hook = home / ".claude" / "hooks" / MODULE.name
            self.assertEqual(
                installed_hook.read_text(encoding="utf-8"),
                MODULE.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
