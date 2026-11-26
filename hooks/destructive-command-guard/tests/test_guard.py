"""Safety tests: command examples are strings and are never executed.

The only child process launched by this suite is guard.py itself, using a
TemporaryDirectory as HOME. Tests do not invoke a shell or a SQL client.
"""

import datetime
import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


GUARD_PATH = Path(__file__).resolve().parents[1] / "guard.py"
SPEC = importlib.util.spec_from_file_location("destructive_guard_under_test", GUARD_PATH)
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)


def sql_command(sql, client="psql"):
    """Construct text for inspection, not an executable command invocation."""
    prefix = {"psql": "psql -c ", "mysql": "mysql -e ", "sqlite3": "sqlite3 demo.db "}[client]
    return prefix + shlex.quote(sql)


class CommandInspectionTests(unittest.TestCase):
    def test_recursive_force_removal_and_wrappers(self):
        commands = [
            "rm -rf /tmp/demo",
            "rm -fr /tmp/demo",
            "rm -r -f /tmp/demo",
            "rm -Rf /tmp/demo",
            "rm --recursive --force /tmp/demo",
            "/bin/rm -rf -- /tmp/demo",
            "rm /tmp/demo -rf",
            "env X=1 rm -rf /tmp/demo",
            "env -u HOME -- rm -rf /tmp/demo",
            "sudo -- rm -rf /tmp/demo",
            "sudo -u root -- rm -rf /tmp/demo",
            "command rm -rf /tmp/demo",
            "exec rm -rf /tmp/demo",
            "X=1 rm -rf /tmp/demo",
            "sh -c 'rm -rf /tmp/demo'",
            "bash -lc 'rm -rf /tmp/demo'",
            "sudo env X=1 bash -lc 'rm -rf /tmp/demo'",
            "echo ok && rm -rf /tmp/demo",
            "false || rm -rf /tmp/demo",
            "echo ok; rm -rf /tmp/demo",
            'echo "$(rm -rf /tmp/demo)"',
            'echo "`rm -rf /tmp/demo`"',
            "rm -r\\\n-f /tmp/demo",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(guard.inspect(command))

    def test_force_push_forms(self):
        commands = [
            "git push --force",
            "git push -f origin main",
            "git -C /tmp/repo push origin --force",
            "git -c color.ui=false push --force origin main",
            "git push --force-with-lease origin main",
            "git push --force-with-lease=main:deadbeef origin main",
            "git push origin +main:main",
            "bash -lc 'git push --force'",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(guard.inspect(command))

    def test_sql_destructive_statements_in_actual_client_arguments(self):
        statements = [
            "DROP TABLE users;",
            "drop table users;",
            "DROP/**/TABLE users;",
            "TRUNCATE TABLE logs;",
            "TRUNCATE logs;",
            "DELETE FROM users;",
            "DELETE FROM users RETURNING 'WHERE';",
            'DELETE FROM "WHERE";',
            "DELETE FROM users /* WHERE id=1 */;",
            "DELETE FROM users -- WHERE id=1\n;",
            "SELECT * FROM users WHERE id=1; DELETE FROM users;",
            "DELETE FROM users WHERE id=1; DELETE FROM sessions;",
            "DELETE FROM users RETURNING (SELECT 1 WHERE true);",
            "WITH removed AS (DELETE FROM users RETURNING id) SELECT * FROM removed WHERE id=1;",
            "DELETE FROM users RETURNING $text$WHERE$text$;",
        ]
        for client in ("psql", "mysql", "sqlite3"):
            for sql in statements:
                with self.subTest(client=client, sql=sql):
                    self.assertTrue(guard.inspect(sql_command(sql, client)))

    def test_client_argument_variants(self):
        commands = [
            "psql --command='DELETE FROM users;'",
            "psql -c'DELETE FROM users;'",
            "mysql --execute='DROP TABLE users;'",
            "mysql -e'TRUNCATE TABLE users;'",
            "sqlite3 -cmd 'DELETE FROM users;' demo.db",
            "sudo -u postgres psql -c 'DELETE FROM users;'",
            "printf '%s\\n' 'DELETE FROM users;' | psql",
            "echo 'DROP TABLE users;' | mysql",
            "psql <<'SQL'\nDELETE FROM users;\nSQL\n",
            "sqlite3 demo.db <<'SQL'\nTRUNCATE users;\nSQL\n",
            "psql <<< 'DELETE FROM users;'",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(guard.inspect(command))

    def test_plain_commands_and_quoted_documentation_are_allowed(self):
        commands = [
            "pwd", "git status", "git push origin main",
            "rm report.tmp", "rm -r /tmp/demo", "rm -f report.tmp",
            "rm -- -rf",
            "git log --grep='git push --force'",
            "echo 'rm -rf /tmp/demo'",
            "printf '%s\\n' 'DROP TABLE users'",
            "echo 'ok; rm -rf /tmp/demo'",
            "echo ok # rm -rf /tmp/demo",
            "# git push --force\nprintf '%s\\n' safe",
            "printf '%s\\n' '$(rm -rf /tmp/demo)'",
            "cat <<'EOF'\nrm -rf /tmp/demo\nDROP TABLE users;\nEOF\n",
            "cat <<'EOF'\n$(rm -rf /tmp/demo)\nEOF\n",
            "cat <<\\EOF\n$(rm -rf /tmp/demo)\nEOF\n",
            "echo 'DROP TABLE users' > notes.txt",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.inspect(command))

    def test_safe_sql_and_statement_scoping(self):
        statements = [
            "SELECT 'DROP TABLE users; DELETE FROM users';",
            "DELETE FROM users WHERE id=1;",
            "DELETE FROM users WHERE id IN (SELECT id FROM inactive);",
            "DELETE FROM users WHERE note='x; DELETE FROM sessions;';",
            "SELECT 1; -- DROP TABLE users",
            "SELECT $tag$DROP TABLE users; DELETE FROM users;$tag$;",
            "DELETE FROM users WHERE id=1; DELETE FROM sessions WHERE id=2;",
            "DELETE FROM users WHERE 1=1;",  # A WHERE presence rule is not a SQL safety proof.
            "SELECT TRUNCATE(1.23, 1);",
            "SELECT (TRUNCATE(1.23, 1));",
        ]
        for client in ("psql", "mysql", "sqlite3"):
            for sql in statements:
                with self.subTest(client=client, sql=sql):
                    self.assertIsNone(guard.inspect(sql_command(sql, client)))

    def test_unquoted_heredoc_executes_substitutions(self):
        command = "cat <<EOF\n'$(rm -rf /tmp/demo)'\nEOF\n"
        self.assertTrue(guard.inspect(command))

    def test_direct_sql_patterns(self):
        for command in ("DROP TABLE users;", "TRUNCATE users;", "DELETE FROM users;"):
            with self.subTest(command=command):
                self.assertTrue(guard.inspect(command))

    def test_incomplete_shell_is_explicitly_uninspectable(self):
        for command in ("echo 'unterminated", "echo $(unterminated", "cat <<EOF\nmissing terminator"):
            with self.subTest(command=command):
                with self.assertRaises(guard.InspectionError):
                    guard.inspect(command)


class HookProtocolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="guard-test-")
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.log = self.home / ".claude" / "hooks" / "blocked.log"
        self.environment = dict(os.environ, HOME=str(self.home), USERPROFILE=str(self.home))

    def invoke(self, event=None, raw=None):
        if raw is None:
            raw = json.dumps(event)
        return subprocess.run(
            [sys.executable, str(GUARD_PATH)],
            input=raw, text=True, capture_output=True, timeout=10,
            cwd=self.home, env=self.environment, check=False,
        )

    def event(self, command, **overrides):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                 "tool_input": {"command": command}, "cwd": "/example/project with spaces"}
        event.update(overrides)
        return event

    def test_blocked_event_exit_message_and_audit_fields(self):
        command = "rm -rf /tmp/demo"
        result = self.invoke(self.event(command))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Destructive command blocked:", result.stderr)
        self.assertIn("rm", result.stderr)
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 1)
        record = json.loads(lines[0])
        self.assertEqual(record["command"], command)
        self.assertEqual(record["project_path"], "/example/project with spaces")
        self.assertTrue(record["reason"])
        self.assertIsNotNone(datetime.datetime.fromisoformat(record["timestamp"]).tzinfo)

    def test_all_five_issue_categories_block_through_stdin(self):
        commands = ["rm -rf /tmp/demo", "git push --force", sql_command("DROP TABLE users;"),
                    sql_command("TRUNCATE users;"), sql_command("DELETE FROM users;")]
        for command in commands:
            with self.subTest(command=command):
                result = self.invoke(self.event(command))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertTrue(result.stderr)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 5)

    def test_allowed_event_is_silent_and_creates_no_log(self):
        result = self.invoke(self.event("git status --short"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertEqual(result.stderr, "")
        self.assertFalse(self.log.exists())

    def test_jsonl_appends_without_record_injection(self):
        commands = ["echo ok\nrm -rf /tmp/demo", "git push --force\n# unicode: 测试"]
        project = '/example/project\n{"forged": true}'
        for command in commands:
            result = self.invoke(self.event(command, cwd=project))
            self.assertEqual(result.returncode, 2, result.stderr)
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        records = [json.loads(line) for line in lines]
        self.assertEqual([item["command"] for item in records], commands)
        self.assertTrue(all(item["project_path"] == project for item in records))

    def test_unwritable_audit_destination_still_blocks(self):
        # A directory where the log file belongs fails even when run as root.
        self.log.mkdir(parents=True)
        result = self.invoke(self.event("rm -rf /tmp/demo"))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertIn("Audit log unavailable", result.stderr)
        self.assertIn("command remains blocked", result.stderr)
        self.assertIn("Destructive command blocked", result.stderr)

    def test_other_tools_and_hook_events_are_ignored(self):
        events = [self.event("rm -rf /tmp/demo", tool_name="Read"),
                  self.event("rm -rf /tmp/demo", hook_event_name="PostToolUse"),
                  {"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": None}]
        for event in events:
            with self.subTest(event=event):
                result = self.invoke(event)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")
        self.assertFalse(self.log.exists())

    def test_malformed_input_fails_closed(self):
        inputs = ["not json", "[]", json.dumps(self.event("ignored", tool_input={})),
                  json.dumps(self.event("echo 'unterminated"))]
        for raw in inputs:
            with self.subTest(raw=raw):
                result = self.invoke(raw=raw)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertIn("Cannot inspect", result.stderr)


if __name__ == "__main__":
    unittest.main()
