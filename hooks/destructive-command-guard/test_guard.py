from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from guard import inspect


class CommandInspectionTests(unittest.TestCase):
    def assertBlocked(self, command: str) -> None:
        self.assertIsNotNone(inspect(command), command)

    def assertAllowed(self, command: str) -> None:
        self.assertIsNone(inspect(command), command)

    def test_recursive_force_remove_flag_order_and_wrappers(self) -> None:
        for command in (
            "rm -rf /tmp/build",
            "rm -fr /tmp/build",
            "rm -r -f /tmp/build",
            "/bin/rm --recursive --force /tmp/build",
            "sudo env rm -Rf /tmp/build",
            "rm file -rf",
            "rm -rfi -- /tmp/build",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_safe_remove_and_quoted_examples_remain_allowed(self) -> None:
        for command in (
            "rm /tmp/one-file",
            "rm -r /tmp/build",
            "rm -f /tmp/one-file",
            "rm -- -rf",
            "echo 'rm -rf /tmp/build'",
            'printf "%s\\n" "rm -rf /tmp/build"',
            "echo safe # rm -rf /tmp/build",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_nested_command_substitutions_are_inspected(self) -> None:
        backtick_command = "echo " + chr(96) + "rm -rf /tmp/build" + chr(96)
        double_quoted_backticks = (
            'echo "' + chr(96) + "rm -rf /tmp/build" + chr(96) + '"'
        )
        for command in (
            "echo $(rm -rf /tmp/build)",
            'echo "$(printf ok; /bin/rm -r -f /tmp/build)"',
            backtick_command,
            "cat <(rm -rf /tmp/build)",
            "echo $(echo $(rm -rf /tmp/build))",
            double_quoted_backticks,
            "eval 'rm -rf /tmp/build'",
            "bash -lc 'rm -rf /tmp/build'",
            "sh -c 'echo before && rm -rf /tmp/build'",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_command_wrappers_and_find_exec_are_inspected(self) -> None:
        for command in (
            "env sh -c 'rm -rf /tmp/build'",
            "sudo sh -c 'rm -rf /tmp/build'",
            "sudo env bash -lc 'git push --force origin main'",
            "env -S \"sh -c 'rm -rf /tmp/build'\"",
            "timeout 10s bash -c 'rm -rf /tmp/build'",
            "xargs -I{} sh -c 'rm -rf /tmp/build'",
            "find /tmp -maxdepth 0 -exec sh -c 'rm -rf /tmp/build' \\;",
            "find . -exec echo safe \\; -exec rm -rf {} \\;",
            "find /tmp -maxdepth 0 -execdir env sh -c 'DROP TABLE users' \\;",
            "busybox sh -c 'TRUNCATE TABLE sessions'",
            "time -p sh -c 'DELETE FROM users'",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_env_attached_split_string_forms(self) -> None:
        for command in (
            "env --split-string='rm -rf /tmp/build'",
            "env -S'rm -rf /tmp/build'",
            "env --split-string='git push --force origin main'",
            "env -S\"sh -c 'DROP TABLE users'\"",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

        for command in (
            "env --split-string='echo safe'",
            "env -S'printf %s harmless'",
            "env --split-string=echo 'rm -rf /tmp/build'",
            "echo \"env --split-string='rm -rf /tmp/build'\"",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_command_arguments_are_not_mistaken_for_executed_commands(self) -> None:
        for command in (
            "echo rm -rf /tmp/build",
            "echo git push --force origin main",
            "echo sh -c 'rm -rf /tmp/build'",
            'echo "first line\nrm -rf /tmp/build"',
            "xargs printf '%s' 'rm -rf /tmp/build'",
            "find /tmp -maxdepth 0 -exec echo 'rm -rf /tmp/build' \\;",
            "find . -exec echo safe \\; -exec echo rm -rf {} \\;",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_quoted_and_commented_substitutions_are_not_executed(self) -> None:
        single_quoted_backticks = (
            "echo '" + chr(96) + "rm -rf /tmp/build" + chr(96) + "'"
        )
        for command in (
            "echo '$(rm -rf /tmp/build)'",
            "echo ok # $(rm -rf /tmp/build)",
            r"echo \$(rm -rf /tmp/build)",
            single_quoted_backticks,
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_force_push_forms_and_prefixes(self) -> None:
        for command in (
            "git push --force origin main",
            "git push -f origin main",
            "git push --force-with-lease origin main",
            "git push --force-if-includes origin main",
            "git push origin +main",
            "git -C repo push -f origin main",
            "sudo git push -f origin main",
            "GIT_TERMINAL_PROMPT=0 git push -f origin main",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_safe_git_and_non_force_options_remain_allowed(self) -> None:
        for command in (
            "git push origin main",
            "git push --dry-run origin main",
            "git status",
            "echo 'git push --force origin main'",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_force_refspec_after_option_terminator(self) -> None:
        for command in (
            "git push -- origin +HEAD:refs/heads/main",
            "git -C repo push -- origin +main",
            "env git push -- origin main +topic:topic",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

        for command in (
            "git push -- origin main",
            "git push -- origin HEAD:refs/heads/main",
            "git push -- --force main",
            "echo 'git push -- origin +main'",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_sql_destructive_statements_and_comments(self) -> None:
        for command in (
            "psql -c 'DROP TABLE users'",
            "mysql --execute='TRUNCATE TABLE sessions'",
            "sqlcmd -Q 'DELETE FROM sessions'",
            "psql --command='DELETE FROM users'",
            "sqlite3 app.db 'DELETE FROM users'",
            "DELETE FROM users",
            "DELETE FROM users -- WHERE id = 1",
            "DELETE FROM users /* WHERE id = 1 */",
            "psql -c 'DELETE FROM users RETURNING $tag$ WHERE $tag$'",
            "mysql -e 'DELETE FROM users # WHERE id = 1'",
            "psql -c 'SELECT 1; DELETE FROM users'",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

    def test_where_clause_must_be_real_and_top_level(self) -> None:
        for command in (
            "psql -c 'DELETE FROM users WHERE id = 1'",
            "sqlite3 app.db 'DELETE FROM users WHERE id IN (SELECT id FROM old_users)'",
            "psql -c 'DELETE FROM users WHERE /* all */ TRUE'",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_sql_pipeline_and_heredoc(self) -> None:
        self.assertBlocked("echo 'DELETE FROM users' | psql")
        self.assertBlocked("psql <<'SQL'\nDELETE FROM users;\nSQL\n")
        self.assertBlocked("bash <<'SH'\nrm -rf /tmp/build\nSH\n")
        self.assertAllowed("cat <<'TEXT'\nrm -rf /tmp/build\nTEXT\n")
        self.assertAllowed("echo 'DELETE FROM users' && psql -c 'SELECT 1'")
        self.assertBlocked("echo ok # <<END\nrm -rf /tmp/build\n")

    def test_shell_and_sql_here_strings(self) -> None:
        for command in (
            "bash <<< 'rm -rf /tmp/build'",
            "sh -s <<< 'git push --force origin main'",
            "psql <<< 'DELETE FROM users'",
            "mysql <<< 'TRUNCATE TABLE sessions'",
        ):
            with self.subTest(command=command):
                self.assertBlocked(command)

        for command in (
            "bash <<< 'echo safe'",
            "bash -c 'echo safe' <<< 'rm -rf /tmp/build'",
            "bash script.sh <<< 'rm -rf /tmp/build'",
            "bash <<< 'rm -rf /tmp/build' script.sh",
            "psql <<< 'DELETE FROM users WHERE id = 1'",
            "psql <<< 'SELECT 1'",
            "echo <<< 'rm -rf /tmp/build'",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_quoted_sql_literals_and_non_sql_commands_remain_allowed(self) -> None:
        for command in (
            "psql -c \"SELECT 'DROP TABLE users'\"",
            "psql -c 'SELECT 1 -- DELETE FROM users'",
            "grep 'DROP TABLE users' migration.sql",
            "echo 'TRUNCATE TABLE users'",
            "psql -c 'DELETE FROM users WHERE id = 3; SELECT 1'",
        ):
            with self.subTest(command=command):
                self.assertAllowed(command)

    def test_malformed_shell_is_denied(self) -> None:
        self.assertBlocked("echo 'unterminated")


class HookProtocolTests(unittest.TestCase):
    def run_hook(self, event: object, *, home: str) -> subprocess.CompletedProcess[str]:
        hook = Path(__file__).with_name("guard.py")
        payload = json.dumps(event) if not isinstance(event, str) else event
        environment = {**os.environ, "HOME": home, "USERPROFILE": home}
        return subprocess.run(
            [sys.executable, str(hook)],
            input=payload,
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )

    def test_block_output_matches_current_pretooluse_format_and_logs_event_cwd(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /tmp/project"},
                    "cwd": "/tmp/project",
                },
                home=home,
            )
            self.assertEqual(result.returncode, 0)
            decision = json.loads(result.stdout)
            output = decision["hookSpecificOutput"]
            self.assertEqual(output["hookEventName"], "PreToolUse")
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn(
                "rm combines recursive deletion", output["permissionDecisionReason"]
            )

            record = json.loads(
                (Path(home) / ".claude/hooks/blocked.log").read_text().splitlines()[0]
            )
            self.assertEqual(record["command"], "rm -rf /tmp/project")
            self.assertEqual(record["project_path"], "/tmp/project")
            self.assertTrue(record["timestamp"].endswith("Z"))
            self.assertEqual(
                (Path(home) / ".claude/hooks/blocked.log").stat().st_mode & 0o777,
                0o600,
            )

    def test_safe_and_unrelated_tools_return_no_decision(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            for event in (
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "npm test"},
                    "cwd": home,
                },
                {"tool_name": "Read", "tool_input": {"file_path": "x"}, "cwd": home},
            ):
                result = self.run_hook(event, home=home)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")
            self.assertFalse((Path(home) / ".claude/hooks/blocked.log").exists())

    def test_malformed_bash_event_is_denied_and_bad_json_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = self.run_hook({"tool_name": "Bash", "tool_input": {}}, home=home)
            self.assertEqual(
                json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"],
                "deny",
            )
            bad_json = self.run_hook("{", home=home)
            self.assertEqual(bad_json.returncode, 2)
            self.assertIn("Invalid PreToolUse JSON", bad_json.stderr)

    def test_log_failure_does_not_allow_a_dangerous_command(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            hooks = Path(home) / ".claude/hooks"
            hooks.mkdir(parents=True)
            (hooks / "blocked.log").mkdir()
            result = self.run_hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git push --force"},
                    "cwd": home,
                },
                home=home,
            )
            output = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(output["permissionDecision"], "deny")
            self.assertIn(
                "audit log could not be written", output["permissionDecisionReason"]
            )


if __name__ == "__main__":
    unittest.main()
