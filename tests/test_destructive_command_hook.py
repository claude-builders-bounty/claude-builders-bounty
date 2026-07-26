from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "hooks" / "block_destructive_commands.py"
INSTALLER = ROOT / "hooks" / "install.py"


class HookTests(unittest.TestCase):
    def run_hook(
        self,
        command: str,
        *,
        tool_name: str = "Bash",
        event_name: str = "PreToolUse",
    ) -> tuple[subprocess.CompletedProcess[str], Path]:
        temporary_home = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_home.cleanup)
        home = Path(temporary_home.name)
        payload = {
            "hook_event_name": event_name,
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": "/projects/example",
        }
        environment = os.environ.copy()
        environment["HOME"] = str(home)
        environment["USERPROFILE"] = str(home)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        return result, home

    def assert_blocked(self, command: str, reason_fragment: str) -> None:
        result, home = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        decision = output["hookSpecificOutput"]
        self.assertEqual(decision["hookEventName"], "PreToolUse")
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn(reason_fragment, decision["permissionDecisionReason"])

        log_path = home / ".claude" / "hooks" / "blocked.log"
        record = json.loads(log_path.read_text(encoding="utf-8"))
        self.assertTrue(record["timestamp"])
        self.assertEqual(record["attempted_command"], command)
        self.assertEqual(record["project_path"], "/projects/example")

    def assert_allowed(self, command: str) -> None:
        result, home = self.run_hook(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_blocks_required_patterns(self) -> None:
        cases = (
            ("rm -rf build", "recursive forced"),
            ("psql -c 'DROP TABLE users'", "DROP TABLE"),
            ("git push --force origin main", "forced Git push"),
            ("psql -c 'TRUNCATE TABLE users'", "TRUNCATE"),
            ("DELETE FROM users", "without a WHERE"),
        )
        for command, reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, reason)

    def test_blocks_adversarial_variants(self) -> None:
        cases = (
            "rm -fr ./build",
            "rm -r -f ./build",
            "RM -Rf ./build",
            "rm --recursive --force ./build",
            "sudo -u root rm --force --recursive ./build",
            "git push -f origin main",
            "git -C repo push origin main --force",
            "mysql -e 'drop\tTABLE audit_log'",
            "delete  from users;",
            "bash -c 'rm -rf /tmp/example'",
        )
        for command in cases:
            with self.subTest(command=command):
                result, _ = self.run_hook(command)
                self.assertEqual(
                    json.loads(result.stdout)["hookSpecificOutput"][
                        "permissionDecision"
                    ],
                    "deny",
                )

    def test_blocks_piped_sql(self) -> None:
        cases = (
            ("printf 'DROP TABLE users;' | psql", "DROP TABLE"),
            ("echo 'TRUNCATE users;' | mysql", "TRUNCATE"),
            ("echo 'DELETE FROM users;' | sqlite3 database.db", "without a WHERE"),
        )
        for command, reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, reason)

    def test_blocks_sql_client_argument_forms(self) -> None:
        cases = (
            ("psql --command='DROP TABLE users'", "DROP TABLE"),
            ("mysql --execute='TRUNCATE users'", "TRUNCATE"),
            ("sqlite3 db.sqlite 'DELETE FROM users'", "without a WHERE"),
            ("psql -c'DROP TABLE audit_log'", "DROP TABLE"),
            ("mysql -e'TRUNCATE audit_log'", "TRUNCATE"),
        )
        for command, reason in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, reason)

    def test_allows_harmless_commands_and_exact_false_positives(self) -> None:
        commands = (
            "ls -la",
            "rm -r build",
            "rm -f output.txt",
            "git push origin main",
            "git push --force-with-lease origin main",
            "SELECT * FROM users",
            "DELETE FROM users WHERE id = 7",
            "echo 'DROP TABLE users'",
            "printf 'TRUNCATE users'",
            "echo 'DELETE FROM users'",
            "grep 'DROP TABLE' schema.sql",
            "python -c \"print('rm -rf /')\"",
            "psql -c \"SELECT 'DROP TABLE users'\"",
            "psql --command='SELECT 1'",
            "mysql --execute='DELETE FROM users WHERE id = 7'",
            "sqlite3 db.sqlite 'DELETE FROM users WHERE id = 7'",
            "sqlite3 db.sqlite '.schema'",
            "# rm -rf /tmp/example",
        )
        for command in commands:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_allows_safe_multiline_delete(self) -> None:
        self.assert_allowed("psql -c 'DELETE FROM users\nWHERE id = 7'")

    def test_detects_unqualified_delete_among_multiple_statements(self) -> None:
        self.assert_blocked(
            "psql -c 'DELETE FROM users WHERE inactive = true; DELETE FROM sessions;'",
            "without a WHERE",
        )

    def test_does_not_interfere_with_other_tools_or_events(self) -> None:
        for tool_name, event_name in (
            ("Read", "PreToolUse"),
            ("Bash", "PostToolUse"),
        ):
            result, home = self.run_hook(
                "rm -rf /tmp/example",
                tool_name=tool_name,
                event_name=event_name,
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((home / ".claude" / "hooks" / "blocked.log").exists())

    def test_malformed_input_fails_open(self) -> None:
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="{not json",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")


class InstallerTests(unittest.TestCase):
    def test_installer_copies_and_registers_hook_idempotently(self) -> None:
        sys.path.insert(0, str(ROOT / "hooks"))
        self.addCleanup(sys.path.remove, str(ROOT / "hooks"))
        import install

        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            settings_path = home / ".claude" / "settings.json"
            settings_path.parent.mkdir(parents=True)
            settings_path.write_text(
                json.dumps({"permissions": {"allow": ["Read"]}}),
                encoding="utf-8",
            )

            destination = install.install(home)
            install.install(home)

            self.assertEqual(
                destination,
                home / ".claude" / "hooks" / "block_destructive_commands.py",
            )
            self.assertEqual(
                destination.read_text(encoding="utf-8"),
                HOOK.read_text(encoding="utf-8"),
            )
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            self.assertEqual(settings["permissions"], {"allow": ["Read"]})
            registrations = settings["hooks"]["PreToolUse"]
            self.assertEqual(len(registrations), 1)
            self.assertEqual(registrations[0]["matcher"], "Bash")
            self.assertIn(
                "block_destructive_commands.py",
                registrations[0]["hooks"][0]["command"],
            )

    def test_documented_one_command_installs_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_home:
            home = Path(temporary_home)
            environment = os.environ.copy()
            environment["HOME"] = str(home)
            environment["USERPROFILE"] = str(home)
            result = subprocess.run(
                [sys.executable, str(INSTALLER)],
                text=True,
                capture_output=True,
                env=environment,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(
                (home / ".claude" / "hooks" / "block_destructive_commands.py").exists()
            )


if __name__ == "__main__":
    unittest.main()
