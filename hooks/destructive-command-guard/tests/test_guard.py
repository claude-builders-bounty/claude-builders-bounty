import json
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime


ROOT = Path(__file__).resolve().parents[1]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".guard-test-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.logs = self.work / "isolated hooks"
        self.project = str(self.work / "project with spaces")

    def event(self, command):
        return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                "cwd": self.project, "tool_input": {"command": command}}

    def invoke(self, event=None, raw=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "guard.py"), "--hooks-dir", str(self.logs)],
            input=raw if raw is not None else json.dumps(event),
            text=True, capture_output=True, timeout=5, cwd=self.work,
        )

    def assert_blocked(self, command):
        result = self.invoke(self.event(command))
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(output["hookEventName"], "PreToolUse")
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertTrue(output["permissionDecisionReason"])
        record = json.loads((self.logs / "blocked.log").read_text().splitlines()[-1])
        self.assertEqual(record["command"], command)
        self.assertEqual(record["cwd"], self.project)
        self.assertIsNotNone(datetime.fromisoformat(record["timestamp"]).tzinfo)
        return output

    def test_recursive_force_removal(self):
        for command in ["rm -rf example", "rm -fr example", "rm -R -f example",
                        "rm --recursive --force example", "sudo -u nobody rm -rf example",
                        "env MODE=test command /bin/rm -rf example",
                        "git status && rm -rf example", "ls; rm -rf example"]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_force_push(self):
        for command in ["git push --force", "git push -f origin main",
                        "git -C 'repo path' push --force origin main",
                        "git -c color.ui=false push --force", "command git push -vf"]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_direct_sql_patterns(self):
        for command in ["DROP TABLE users", "drop table if exists users;",
                        "TRUNCATE users", "TRUNCATE TABLE users;",
                        "DELETE FROM users", "delete\nfrom users;"]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_sql_client_arguments(self):
        for command in [
            'psql -d example -c "DROP TABLE users;"',
            "psql --command='TRUNCATE TABLE users'",
            'mysql -e "DELETE FROM users"',
            "mariadb --execute='DROP TABLE users'",
            "sqlite3 example.db 'DELETE FROM users;'",
            "sqlite3 -cmd 'DROP TABLE users' example.db",
            "duckdb example.db -c 'TRUNCATE users'",
            "sqlcmd -Q 'DELETE FROM users'",
        ]:
            with self.subTest(command=command):
                self.assert_blocked(command)

    def test_where_must_belong_to_the_delete_statement(self):
        for query in [
            "DELETE FROM users; SELECT * FROM users WHERE id = 1",
            "DELETE FROM users /* WHERE id = 1 */",
            "DELETE FROM users -- WHERE id = 1\n;",
            "DELETE FROM users RETURNING 'WHERE'",
            'DELETE FROM "WHERE"',
            "DELETE FROM users WHERE id = 1; DELETE FROM sessions;",
        ]:
            with self.subTest(query=query):
                self.assert_blocked("psql -c " + shlex.quote(query))

    def test_normal_commands_and_literal_text_are_untouched(self):
        commands = [
            "ls -la", "git status", "git push origin main", "git push --force-with-lease",
            "python3 -m unittest", "npm test", "rm obsolete.txt", "rm -r old-directory",
            "echo 'rm -rf /'", "printf '%s\\n' 'DROP TABLE users; TRUNCATE users'",
            "grep -n 'DELETE FROM' schema.sql", "rg 'git push --force' README.md",
            "git log --grep='DROP TABLE'", "command -v rm", "sudo --list",
            "echo 'a; rm -rf example'", "echo ok # rm -rf example",
            "echo 'Unicode café 日本語'", "", "  \n  ",
            "psql -c 'SELECT 1'", "psql -c 'DELETE FROM users WHERE id = 1'",
            "sqlite3 example.db 'DELETE FROM users WHERE active = 0'",
            'psql -c "SELECT \'DROP TABLE users\', \'DELETE FROM users\'"',
        ]
        for command in commands:
            with self.subTest(command=command):
                result = self.invoke(self.event(command))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(result.stderr, "")
        self.assertFalse(self.logs.exists())

    def test_other_events_and_tools_are_ignored(self):
        for field, value in [("hook_event_name", "PostToolUse"), ("tool_name", "Write")]:
            event = self.event("rm -rf example")
            event[field] = value
            result = self.invoke(event)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
        self.assertFalse(self.logs.exists())

    def test_quoted_heredoc_prints_literal_text_without_false_block(self):
        for command in [
            "cat <<'EOF'\nrm -rf scratch\nDROP TABLE users;\nEOF\n",
            'cat <<"TEXT"\nTRUNCATE users;\nDELETE FROM users;\nTEXT\n',
            "cat > example.txt <<'EOF'\ngit push --force\nEOF\n",
            "cat <<-'EOF'\n\trm -rf scratch\n\tEOF\n",
        ]:
            with self.subTest(command=command):
                result = self.invoke(self.event(command))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")
        self.assertFalse(self.logs.exists())

    def test_command_after_literal_heredoc_is_still_checked(self):
        self.assert_blocked("cat <<'EOF'\nrm -rf printed-text\nEOF\nrm -rf actual-target")

    def test_invalid_input_does_not_silently_allow(self):
        for raw in ["not JSON", "[]", json.dumps(self.event(None)),
                    json.dumps(self.event("rm 'unfinished"))]:
            with self.subTest(raw=raw):
                result = self.invoke(raw=raw)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]
                                 ["permissionDecision"], "deny")

    def test_log_is_one_line_per_attempt_and_uses_event_directory(self):
        self.project += "\nsecond line"
        self.assert_blocked("rm -rf example\necho 'not executed'")
        self.assert_blocked("git push --force")
        lines = (self.logs / "blocked.log").read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["cwd"], self.project)
        self.assertNotEqual(self.project, str(self.work))

    def test_log_failure_does_not_allow_a_blocked_command(self):
        self.logs.write_text("This is a file, not a log directory")
        result = self.invoke(self.event("rm -rf example"))
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("log", decision["permissionDecisionReason"].lower())

    def test_input_command_is_never_executed(self):
        marker = self.work / "must-not-be-created"
        result = self.invoke(self.event("touch " + str(marker)))
        self.assertEqual(result.stdout, "")
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
