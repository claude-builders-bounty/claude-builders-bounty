"""Black-box tests for the hook; command strings are never executed.

Only the Python hook is launched. A temporary HOME isolates every audit log
from the developer's real Claude configuration.
"""

import datetime
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).resolve().parents[1] / "hooks" / "block_destructive_commands.py"


class DestructiveCommandHookTests(unittest.TestCase):
    def setUp(self):
        self.temporary_home = tempfile.TemporaryDirectory(prefix="hook-test-")
        self.addCleanup(self.temporary_home.cleanup)
        self.home = Path(self.temporary_home.name)
        self.project = self.home / "project with spaces"
        self.project.mkdir()
        self.log = self.home / ".claude" / "hooks" / "blocked.log"

    def invoke_raw(self, text):
        environment = os.environ.copy()
        environment["HOME"] = str(self.home)
        # The shell is never invoked: the potentially destructive command stays
        # inside JSON sent on stdin, rather than becoming a process argument.
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=text,
            text=True,
            capture_output=True,
            env=environment,
            cwd=self.project,
            timeout=5,
            check=False,
        )

    def invoke(self, command, tool_name="Bash"):
        return self.invoke_raw(json.dumps({
            "tool_name": tool_name,
            "tool_input": {"command": command},
            "cwd": str(self.project),
        }))

    def assert_allowed(self, command):
        result = self.invoke(command)
        self.assertEqual(result.returncode, 0, (command, result.stderr))
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")

    def assert_blocked(self, command):
        result = self.invoke(command)
        self.assertEqual(result.returncode, 2, (command, result.stderr))
        self.assertEqual(result.stdout, "")
        self.assertTrue(result.stderr.strip(), "A denial needs a readable reason")
        self.assertNotIn("Traceback", result.stderr)
        return result

    def test_recursive_force_rm_is_blocked(self):
        for command in (
            "rm -rf /tmp/hook-fixture",
            "rm -fr /tmp/hook-fixture",
            "rm -r -f /tmp/hook-fixture",
            "rm -f -r /tmp/hook-fixture",
            "rm --recursive --force /tmp/hook-fixture",
            "rm --force -R /tmp/hook-fixture",
            "rm -rf -- /tmp/hook-fixture",
            "sudo rm -rf /tmp/hook-fixture",
            "/bin/rm -rf /tmp/hook-fixture",
            "true && rm -rf /tmp/hook-fixture",
            "printf ready; rm -r -f /tmp/hook-fixture",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_nonrecursive_rm_and_filename_arguments_are_allowed(self):
        for command in (
            "rm -f /tmp/hook-fixture",
            "rm -r /tmp/hook-fixture",
            "rm -- /tmp/hook-fixture-rf",
            "rm -f -- -r",
            "rm './report -rf.txt'",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)
        self.assertFalse(self.log.exists())

    def test_git_force_push_variants_are_blocked(self):
        for command in (
            "git push --force origin main",
            "git push -f origin feature",
            "git push --force=true origin main",
            "git push --force-with-lease origin main",
            "git push --force-with-lease=main:abc123 origin main",
            "git -C /tmp/hook-repository push --force origin main",
            "git push --force-if-includes -f origin main",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_ordinary_git_commands_are_allowed(self):
        for command in (
            "git status --short",
            "git push origin feature",
            "git push --force-if-includes origin feature",
            "git diff --force",
            "git push origin refs/heads/force-work",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)
        self.assertFalse(self.log.exists())

    def test_destructive_sql_is_blocked(self):
        for command in (
            "sqlite3 local.db 'DROP TABLE users;'",
            "sqlite3 local.db 'drop table if exists users;'",
            "psql -c 'TRUNCATE TABLE users;'",
            "psql -c 'TRUNCATE users;'",
            "sqlite3 local.db 'DELETE FROM users;'",
            "sqlite3 local.db 'delete from users;'",
            "sqlite3 local.db 'SELECT 1; DELETE FROM users;'",
            "sqlite3 local.db 'DELETE FROM users; SELECT 1 WHERE 1 = 1;'",
            "sqlite3 local.db 'DELETE FROM users /* WHERE id = 1 */;'",
            "sqlite3 local.db \"DELETE FROM users RETURNING 'WHERE';\"",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_read_queries_and_filtered_deletes_are_allowed(self):
        for command in (
            "sqlite3 local.db 'SELECT * FROM users;'",
            "sqlite3 local.db 'DELETE FROM users WHERE id = 1;'",
            "psql -c 'delete from users where disabled = true;'",
            "sqlite3 local.db \"SELECT 'DROP TABLE users;';\"",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)
        self.assertFalse(self.log.exists())

    def test_dangerous_text_in_echo_printf_and_comments_is_allowed(self):
        for command in (
            "echo 'rm -rf /tmp/hook-fixture'",
            "printf '%s\\n' 'git push --force origin main'",
            "echo 'DROP TABLE users; DELETE FROM users;'",
            "printf '%s' 'TRUNCATE TABLE users;'",
            "# rm -rf /tmp/hook-fixture\nprintf safe",
            "git status # git push --force origin main",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)
        self.assertFalse(self.log.exists())

    def test_literal_shell_command_arguments_are_inspected(self):
        for command in (
            "bash -c 'rm -rf /tmp/hook-fixture'",
            "bash -lc 'git push --force origin main'",
            "sh -c 'printf ready; rm -r -f /tmp/hook-fixture'",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        for command in (
            "bash -c 'git status --short'",
            "bash -lc 'printf safe'",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_executed_command_substitutions_are_inspected(self):
        for command in (
            "echo $(rm -rf /tmp/hook-fixture)",
            'printf "%s" "$(git push --force origin main)"',
            "echo `rm -rf /tmp/hook-fixture`",
            'printf "%s" "`git push --force origin main`"',
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        for command in (
            "echo '$(rm -rf /tmp/hook-fixture)'",
            "echo '`rm -rf /tmp/hook-fixture`'",
            r'echo "\$(rm -rf /tmp/hook-fixture)"',
            r'echo "\`rm -rf /tmp/hook-fixture\`"',
            "printf '%s' \"$(printf safe)\"",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_only_an_outer_sql_where_clause_guards_delete(self):
        for command in (
            "psql -c 'DELETE FROM users USING (SELECT id FROM inactive WHERE disabled = true) AS inactive;'",
            "sqlite3 local.db 'DELETE FROM \"WHERE\";'",
            "mysql -e 'DELETE FROM `WHERE`;'",
            "sqlite3 local.db 'DELETE FROM [WHERE];'",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        self.assert_allowed(
            "psql -c 'DELETE FROM users USING (SELECT id FROM inactive WHERE disabled = true) AS inactive WHERE users.id = inactive.id;'"
        )

    def test_literal_sql_pipelines_and_here_strings_are_inspected(self):
        for command in (
            "echo 'DELETE FROM users;' | sqlite3 local.db",
            "printf '%s\\n' 'DROP TABLE users;' | sqlite3 local.db",
            "sqlite3 local.db <<< 'DELETE FROM users;'",
            "psql <<< 'TRUNCATE TABLE users;'",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        for command in (
            "printf '%s\\n' 'SELECT * FROM users;' | sqlite3 local.db",
            "echo 'DELETE FROM users WHERE id = 1;' | sqlite3 local.db",
            "sqlite3 local.db <<< 'SELECT * FROM users;'",
            "cat <<< 'rm -rf /tmp/hook-fixture'",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_heredoc_data_and_executed_substitutions_are_distinguished(self):
        for command in (
            "sqlite3 local.db <<'SQL'\nDELETE FROM users;\nSQL\n",
            "psql <<SQL\nDROP TABLE users;\nSQL\n",
            "cat <<TEXT\n$(rm -rf /tmp/hook-fixture)\nTEXT\n",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        for command in (
            "sqlite3 local.db <<'SQL'\nDELETE FROM users WHERE id = 1;\nSQL\n",
            "cat <<'TEXT'\nrm -rf /tmp/hook-fixture\nDROP TABLE users;\nTEXT\n",
            "cat <<'TEXT'\n$(rm -rf /tmp/hook-fixture)\nTEXT\n",
            "cat <<TEXT\nrm -rf /tmp/hook-fixture\nTEXT\n",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_unterminated_shell_quotes_are_blocked(self):
        for command in (
            "echo 'unfinished",
            'printf "%s" "unfinished',
            "bash -c \"echo 'unfinished\"",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_newlines_and_comments_do_not_hide_executed_commands(self):
        for command in (
            "printf safe\nrm -rf /tmp/hook-fixture",
            "printf safe # harmless first line\nrm -rf /tmp/hook-fixture",
            "# explanation\ngit push --force origin main",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        for command in (
            "echo ';' rm -rf /tmp/hook-fixture",
            "echo '&&' git push --force origin main",
            "printf '%s' 'safe\nrm -rf /tmp/hook-fixture'",
        ):
            with self.subTest(command=command):
                self.assert_allowed(command)

    def test_redirections_groups_and_loop_conditions_are_inspected(self):
        for command in (
            ">out.log rm -rf /tmp/hook-fixture",
            "2>out.log rm -rf /tmp/hook-fixture",
            "{ rm -rf /tmp/hook-fixture; }",
            "while rm -rf /tmp/hook-fixture; do printf waiting; done",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_sql_dialect_comments_and_dollar_strings_do_not_guard_delete(self):
        for command in (
            "mysql -e 'DELETE FROM accounts # WHERE id = 1'",
            "psql -c 'DELETE FROM accounts RETURNING $$ WHERE $$;'",
            "psql -c 'DELETE FROM accounts RETURNING $tag$ WHERE $tag$;'",
            "mysql -e 'DROP TEMPORARY TABLE accounts;'",
        ):
            with self.subTest(command=command):
                self.assert_blocked(command)
        self.assert_allowed("sqlite3 data.db 'SELECT truncate FROM metrics;'")

    def test_sql_heredoc_remains_associated_with_piped_client(self):
        self.assert_blocked(
            "sqlite3 data.db <<EOF | cat\nDELETE FROM accounts;\nEOF\n"
        )
        self.assert_allowed(
            "sqlite3 data.db <<EOF | cat\nSELECT * FROM accounts;\nEOF\n"
        )

    def test_non_bash_tools_are_ignored(self):
        result = self.invoke("rm -rf /tmp/hook-fixture", tool_name="Read")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.log.exists())

    def test_malformed_json_and_invalid_bash_payloads_are_blocked(self):
        for text in (
            "{",
            "",
            "null",
            "[]",
            json.dumps({"tool_name": "Bash"}),
            json.dumps({"tool_name": "Bash", "tool_input": {}}),
            json.dumps({"tool_name": "Bash", "tool_input": []}),
            json.dumps({"tool_name": "Bash", "tool_input": {"command": 123}}),
        ):
            with self.subTest(payload=text):
                result = self.invoke_raw(text)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr.strip())
                self.assertNotIn("Traceback", result.stderr)

    def test_denial_appends_timestamp_command_path_and_reason(self):
        commands = [
            "rm -rf /tmp/hook-fixture-one",
            "git push --force origin feature",
        ]
        for command in commands:
            self.assert_blocked(command)
        records = [json.loads(line) for line in self.log.read_text().splitlines()]
        self.assertEqual(len(records), 2)
        for command, record in zip(commands, records):
            self.assertEqual(record["command"], command)
            self.assertEqual(record["project_path"], str(self.project))
            self.assertTrue(record["reason"].strip())
            timestamp = datetime.datetime.fromisoformat(
                record["timestamp"].replace("Z", "+00:00")
            )
            self.assertIsNotNone(timestamp.tzinfo)

    def test_multiline_command_cannot_forge_additional_jsonl_records(self):
        command = 'rm -rf /tmp/hook-fixture\n# {"reason":"forged"}\n'
        self.assert_blocked(command)
        lines = self.log.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["command"], command)
        self.assertNotEqual(record["reason"], "forged")

    @unittest.skipIf(os.name == "nt", "POSIX file permissions")
    def test_audit_log_is_private(self):
        self.assert_blocked("rm -rf /tmp/hook-fixture")
        self.assertEqual(stat.S_IMODE(self.log.stat().st_mode), 0o600)

    def test_audit_write_failure_does_not_allow_command(self):
        # A regular file where a directory is needed fails on every platform,
        # including privileged test runners for which chmod is not sufficient.
        (self.home / ".claude").write_text("directory deliberately unavailable")
        self.assert_blocked("rm -rf /tmp/hook-fixture")
        self.assertFalse(self.log.exists())

    @unittest.skipIf(os.name == "nt", "POSIX symlink handling")
    def test_audit_log_symlink_is_not_followed_and_command_stays_blocked(self):
        target = self.home / "unrelated-file.txt"
        sentinel = "This file must not be changed by audit logging.\n"
        target.write_text(sentinel)
        self.log.parent.mkdir(parents=True)
        self.log.symlink_to(target)
        self.assert_blocked("rm -rf /tmp/hook-fixture")
        self.assertTrue(self.log.is_symlink())
        self.assertEqual(target.read_text(), sentinel)


if __name__ == "__main__":
    unittest.main()
