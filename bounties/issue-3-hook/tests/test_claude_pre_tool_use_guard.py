import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

MODULE_PATH = Path(__file__).resolve().parents[1] / "claude_pre_tool_use_guard.py"
spec = importlib.util.spec_from_file_location("guard", MODULE_PATH)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class DetectionTests(unittest.TestCase):
    def assert_blocked(self, command, rule=None):
        decision = guard.detect_dangerous_command(command)
        self.assertIsNotNone(decision, command)
        if rule:
            self.assertEqual(decision.rule, rule)

    def assert_allowed(self, command):
        self.assertIsNone(guard.detect_dangerous_command(command), command)

    def test_blocks_rm_rf_variants(self):
        self.assert_blocked("rm -rf build", "rm-rf")
        self.assert_blocked("sudo rm -fr /tmp/demo", "rm-rf")
        self.assert_blocked("env FOO=1 /bin/rm --recursive --force ./dist", "rm-rf")

    def test_blocks_rm_rf_in_shell_control_contexts(self):
        self.assert_blocked("if true; then rm -rf build; fi", "rm-rf")
        self.assert_blocked('for d in build; do rm -rf "$d"; done', "rm-rf")
        self.assert_blocked("find build -type d | xargs -I {} rm -rf {}", "rm-rf")
        self.assert_blocked("echo $(rm -rf build)", "rm-rf")
        self.assert_blocked('printf "$(rm -rf build)"', "rm-rf")
        self.assert_blocked("echo `rm -rf build`", "rm-rf")

    def test_allows_normal_rm_and_safe_commands(self):
        self.assert_allowed("rm -r build")
        self.assert_allowed("rm -f output.txt")
        self.assert_allowed("npm test && git status")

    def test_blocks_force_push(self):
        self.assert_blocked("git push --force origin main", "git-force-push")
        self.assert_blocked("git push -f", "git-force-push")
        self.assert_blocked("git push origin +HEAD:main", "git-force-push")
        self.assert_blocked("git push --force-with-lease", "git-force-push")
        self.assert_blocked("git push -fu origin main", "git-force-push")
        self.assert_blocked("git push -uf origin main", "git-force-push")
        self.assert_blocked("git push -vf origin main", "git-force-push")

    def test_blocks_force_push_with_global_git_options(self):
        self.assert_blocked("git -C repo push --force origin main", "git-force-push")
        self.assert_blocked("git -c core.sshCommand=ssh push --force-with-lease", "git-force-push")
        self.assert_blocked("git --git-dir=.git push origin +HEAD:main", "git-force-push")
        self.assert_blocked("git -p push --force origin main", "git-force-push")

    def test_allows_normal_git_push(self):
        self.assert_allowed("git push origin main")

    def test_blocks_sql_destructive_statements(self):
        self.assert_blocked('psql -c "DROP TABLE users"', "sql-drop-table")
        self.assert_blocked('mysql -e "TRUNCATE TABLE sessions"', "sql-truncate")
        self.assert_blocked('sqlite3 app.db "DELETE FROM users"', "sql-delete-without-where")
        self.assert_blocked('echo "DROP TABLE users" | psql "$DATABASE_URL"', "sql-drop-table")

    def test_delete_from_requires_where(self):
        self.assert_allowed('psql -c "DELETE FROM users WHERE id = 1"')
        self.assert_allowed('psql -c "DELETE FROM users\nWHERE id = 1"')
        self.assert_blocked('psql -c "DELETE FROM users;"', "sql-delete-without-where")
        self.assert_blocked('DELETE FROM users', "sql-delete-without-where")
        self.assert_blocked('psql -c "DELETE FROM users /* WHERE fake */"', "sql-delete-without-where")

    def test_sql_string_comments_do_not_hide_later_destructive_sql(self):
        self.assert_blocked('psql -c "SELECT \'--\'; DROP TABLE users"', "sql-drop-table")
        self.assert_blocked('psql -c "SELECT \'--\'; DELETE FROM users"', "sql-delete-without-where")
        self.assert_blocked('psql -c "SELECT \'--\'; TRUNCATE users"', "sql-truncate")
        self.assert_blocked("psql -c 'SELECT $$--$$; DROP TABLE users'", "sql-drop-table")
        self.assert_blocked("psql -c 'SELECT $$--$$; DELETE FROM users'", "sql-delete-without-where")
        self.assert_blocked("psql -c 'SELECT $$--$$; TRUNCATE users'", "sql-truncate")

    def test_allows_text_search_mentions(self):
        self.assert_allowed('grep "DROP TABLE" docs/schema.md')
        self.assert_allowed('rg "DELETE FROM" README.md')


class HookProtocolTests(unittest.TestCase):
    def test_non_bash_tool_passes(self):
        self.assertIsNone(guard.run_hook({"hook_event_name": "PreToolUse", "tool_name": "Read", "tool_input": {}}))

    def test_safe_bash_tool_passes_without_output(self):
        self.assertIsNone(
            guard.run_hook(
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "cwd": "/tmp/project",
                    "tool_input": {"command": "git status"},
                }
            )
        )

    def test_block_payload_and_logging(self):
        with tempfile.TemporaryDirectory() as td:
            log_path = Path(td) / "blocked.log"
            with mock.patch.object(guard, "LOG_PATH", log_path):
                payload = guard.run_hook(
                    {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "cwd": "/tmp/project",
                        "tool_input": {"command": "rm -rf build"},
                    }
                )
                entries = [json.loads(line) for line in log_path.read_text().splitlines()]

        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("rm -rf", payload["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertEqual(entries[0]["command"], "rm -rf build")
        self.assertEqual(entries[0]["project_path"], "/tmp/project")
        self.assertEqual(entries[0]["rule"], "rm-rf")
        self.assertIn("timestamp", entries[0])


if __name__ == "__main__":
    unittest.main()
