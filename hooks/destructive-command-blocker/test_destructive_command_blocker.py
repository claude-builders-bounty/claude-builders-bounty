#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("destructive-command-blocker.py")
INSTALLER = Path(__file__).with_name("install.py")


class DestructiveCommandBlockerTests(unittest.TestCase):
    def run_hook(
        self,
        command: str,
        hooks_dir: Path,
        *,
        tool_name: str = "Bash",
        raw_input: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": tool_name,
            "tool_input": {"command": command, "cwd": "/tmp/example-project"},
        }
        env = os.environ.copy()
        env["CLAUDE_HOOKS_DIR"] = str(hooks_dir)
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=raw_input if raw_input is not None else json.dumps(payload),
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def assert_blocked(self, command: str, expected_rule: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            result = self.run_hook(command, hooks_dir)

            self.assertEqual(result.returncode, 0)
            response = json.loads(result.stdout)
            hook_output = response["hookSpecificOutput"]
            self.assertEqual(hook_output["hookEventName"], "PreToolUse")
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn(expected_rule, hook_output["permissionDecisionReason"])

            log_path = hooks_dir / "blocked.log"
            self.assertTrue(log_path.exists())
            log_event = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(log_event["command"], command)
            self.assertEqual(log_event["project_path"], "/tmp/example-project")
            self.assertEqual(log_event["rule"], expected_rule)
            self.assertEqual(log_event["pattern"], expected_rule)
            self.assertIn("reason", log_event)
            self.assertIn("evidence", log_event)
            self.assertIn("severity", log_event)

    def assert_allowed(self, command: str, *, tool_name: str = "Bash", raw_input: str | None = None) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            result = self.run_hook(command, hooks_dir, tool_name=tool_name, raw_input=raw_input)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse((hooks_dir / "blocked.log").exists())

    def test_blocks_required_acceptance_patterns(self) -> None:
        cases = [
            ("rm -rf build", "rm -rf"),
            ('psql -c "DROP TABLE users"', "DROP TABLE"),
            ("git push origin main --force", "git push --force"),
            ('mysql -e "TRUNCATE TABLE sessions"', "TRUNCATE"),
            ('psql -c "DELETE FROM users"', "DELETE FROM without WHERE"),
        ]
        for command, expected_rule in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, expected_rule)

    def test_blocks_rm_variants_and_wrappers(self) -> None:
        cases = [
            "rm -fr build",
            "rm -Rf ./dist",
            "sudo command rm --recursive --force ./dist",
            'bash -lc "rm -rf build"',
            "find . -exec rm -rf {} +",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, "rm -rf")

    def test_blocks_git_force_push_variants(self) -> None:
        cases = [
            "git -C repo push origin main --force-with-lease",
            "git push origin +main",
            "sudo git push -f origin HEAD",
        ]
        for command in cases:
            with self.subTest(command=command):
                expected = "git push forced refspec" if "+main" in command else "git push --force"
                self.assert_blocked(command, expected)

    def test_blocks_sql_client_payloads(self) -> None:
        cases = [
            ('echo "DROP TABLE users" | psql mydb', "DROP TABLE"),
            ("echo DROP TABLE users | psql mydb", "DROP TABLE"),
            ('printf "DROP TABLE users;" | psql mydb', "DROP TABLE"),
            ('sqlite3 app.db "DELETE FROM users"', "DELETE FROM without WHERE"),
            ('mysql --execute="DROP DATABASE prod"', "DROP DATABASE"),
            ('sqlcmd -Q "TRUNCATE TABLE dbo.sessions"', "TRUNCATE"),
            ('docker exec db psql -c "DELETE FROM audit_log"', "DELETE FROM without WHERE"),
            ("psql <<SQL\nDROP TABLE users;\nSQL", "DROP TABLE"),
        ]
        for command, expected_rule in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, expected_rule)

    def test_blocks_direct_destructive_sql_statements(self) -> None:
        cases = [
            ("DROP TABLE users", "DROP TABLE"),
            ("TRUNCATE audit_log", "TRUNCATE"),
            ("DELETE FROM sessions", "DELETE FROM without WHERE"),
            ("-- maintenance\nDROP TABLE stale_sessions", "DROP TABLE"),
            ("echo done; DELETE FROM audit_log", "DELETE FROM without WHERE"),
        ]
        for command, expected_rule in cases:
            with self.subTest(command=command):
                self.assert_blocked(command, expected_rule)

    def test_blocks_destructive_sql_from_input_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "project"
            hooks_dir = Path(tmpdir) / "hooks"
            workdir.mkdir()
            hooks_dir.mkdir()

            files = {
                "drop.sql": "DROP TABLE users;\n",
                "drop_schema.sql": "DROP SCHEMA private;\n",
                "truncate.sql": "TRUNCATE TABLE audit_log;\n",
                "delete.sql": "DELETE FROM sessions;\n",
                "prod": "DROP TABLE production_users;\n",
                "DROP TABLE users.sql": "DELETE FROM sessions WHERE expires_at < now();\n",
                "safe.sql": "DELETE FROM sessions WHERE expires_at < now();\n",
            }
            for filename, contents in files.items():
                (workdir / filename).write_text(contents, encoding="utf-8")

            blocked_cases = [
                ("psql -f drop.sql", "DROP TABLE"),
                ("psql --file=drop_schema.sql", "DROP SCHEMA"),
                ("sqlcmd -i truncate.sql", "TRUNCATE"),
                ("mysql < delete.sql", "DELETE FROM without WHERE"),
                ("cat drop.sql | psql mydb", "DROP TABLE"),
            ]
            for command, expected_rule in blocked_cases:
                with self.subTest(command=command):
                    payload = {
                        "tool_name": "Bash",
                        "tool_input": {"command": command, "cwd": str(workdir)},
                    }
                    result = self.run_hook(command, hooks_dir, raw_input=json.dumps(payload))
                    self.assertEqual(result.returncode, 0)
                    response = json.loads(result.stdout)
                    reason = response["hookSpecificOutput"]["permissionDecisionReason"]
                    self.assertIn(expected_rule, reason)
                    self.assertIn("SQL input file", reason)

            safe_payload = {
                "tool_name": "Bash",
                "tool_input": {
                    "command": 'psql -f safe.sql && mysql -f prod && psql -f "DROP TABLE users.sql"',
                    "cwd": str(workdir),
                },
            }
            safe_result = self.run_hook("", hooks_dir, raw_input=json.dumps(safe_payload))
            self.assertEqual(safe_result.returncode, 0)
            self.assertEqual(safe_result.stdout, "")

    def test_allows_safe_commands_and_false_positive_strings(self) -> None:
        cases = [
            "git status --short",
            "rm -f build.log",
            "rm -r old-cache",
            'echo "rm -rf build"',
            'printf "git push --force"',
            'grep -R "DROP TABLE" docs',
            "printf 'DELETE FROM users' >> examples.sql",
            "DELETE FROM users WHERE id = 1",
            'psql -c "DELETE FROM users WHERE id = 1"',
            "psql -c \"SELECT 'DELETE FROM users' AS example\"",
        ]
        for command in cases:
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_ignores_non_bash_tool_and_invalid_input(self) -> None:
        self.assert_allowed("rm -rf build", tool_name="Read")
        self.assert_allowed("", raw_input="{not json")

    def test_project_path_fallback_uses_transcript_parent(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            hooks_dir = Path(tmpdir)
            payload = {
                "tool_name": "Bash",
                "tool_input": {"command": "rm -rf build"},
                "transcript_path": "/tmp/example-project/.claude/session.jsonl",
            }
            result = self.run_hook("", hooks_dir, raw_input=json.dumps(payload))

            self.assertEqual(result.returncode, 0)
            log_event = json.loads((hooks_dir / "blocked.log").read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(log_event["project_path"], "/tmp/example-project/.claude")

    def test_installer_is_idempotent_and_preserves_existing_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            claude_dir = Path(tmpdir)
            settings_path = claude_dir / "settings.json"
            settings_path.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "PreToolUse": [
                                {
                                    "matcher": "Edit",
                                    "hooks": [{"type": "command", "command": "echo edit"}],
                                }
                            ]
                        }
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["CLAUDE_CONFIG_DIR"] = str(claude_dir)

            for _ in range(2):
                result = subprocess.run(
                    [sys.executable, str(INSTALLER)],
                    text=True,
                    capture_output=True,
                    env=env,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            pre_tool_use = settings["hooks"]["PreToolUse"]
            blocker_entries = [
                entry
                for entry in pre_tool_use
                for hook in entry.get("hooks", [])
                if "destructive-command-blocker.py" in hook.get("command", "")
            ]
            self.assertEqual(len(blocker_entries), 1)
            self.assertTrue((claude_dir / "hooks" / "destructive-command-blocker.py").exists())
            self.assertTrue(any(entry.get("matcher") == "Edit" for entry in pre_tool_use))


if __name__ == "__main__":
    unittest.main()
