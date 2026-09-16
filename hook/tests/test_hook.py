"""Test suite for pretooluse_bash_guard (stdlib unittest, 45+ cases)."""
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pretooluse_bash_guard as g  # noqa: E402


class HookTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["HOOK_BLOCKED_LOG"] = str(Path(self._tmp.name) / "blocked.log")
        os.environ.pop("HOOK_DISABLE_RULES", None)
        os.environ["HOOK_ALLOW_SAFE_RM_TARGETS"] = "1"
        self.err = io.StringIO()

    def tearDown(self):
        self._tmp.cleanup()
        os.environ.pop("HOOK_BLOCKED_LOG", None)
        os.environ.pop("HOOK_ALLOW_SAFE_RM_TARGETS", None)

    def call(self, cmd, tool="Bash"):
        payload = {
            "hook_event_name": "PreToolUse",
            "tool_name": tool,
            "tool_input": {"command": cmd},
            "cwd": "/project",
            "session_id": "test-session",
        }
        out = io.StringIO()
        with redirect_stderr(self.err), redirect_stdout(out):
            code = g.run(payload)
        self.stdout_json = out.getvalue().strip()
        return code

    def log_lines(self):
        p = Path(self._tmp.name) / "blocked.log"
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]

    # ---------- rm -rf: blocked ----------
    def test_rm_rf_root(self):
        self.assertEqual(self.call("rm -rf /"), 2)
        self.assertIn("rm-rf", [l["rule"] for l in self.log_lines()])

    def test_rm_rf_home(self):
        self.assertEqual(self.call("rm -rf ~"), 2)

    def test_rm_fr_merged(self):
        self.assertEqual(self.call("rm -fr /tmp/data"), 2)

    def test_rm_separate_flags(self):
        self.assertEqual(self.call("rm -r -f x"), 2)

    def test_rm_long_flags(self):
        self.assertEqual(self.call("rm --recursive --force x"), 2)

    def test_rm_Rf(self):
        self.assertEqual(self.call("rm -Rf important.db"), 2)

    def test_rm_sudo_prefix(self):
        self.assertEqual(self.call("sudo rm -rf /etc"), 2)

    def test_rm_in_chain(self):
        self.assertEqual(self.call("ls && rm -rf /"), 2)

    def test_rm_in_semicolon(self):
        self.assertEqual(self.call("echo hi; rm -rf /home"), 2)

    def test_rm_mixed_targets_blocks(self):
        self.assertEqual(self.call("rm -rf node_modules backup.sql"), 2)

    def test_rm_quoted_flag(self):
        self.assertEqual(self.call('rm "-rf" /weird'), 2)

    # ---------- rm: allowed ----------
    def test_rm_single_file(self):
        self.assertEqual(self.call("rm file.txt"), 0)

    def test_rm_recursive_only(self):
        self.assertEqual(self.call("rm -r dir"), 0)

    def test_rm_force_only(self):
        self.assertEqual(self.call("rm -f file.txt"), 0)

    def test_rm_rf_node_modules_allowed(self):
        self.assertEqual(self.call("rm -rf node_modules"), 0)

    def test_rm_rf_dot_slash_build_allowed(self):
        self.assertEqual(self.call("rm -rf ./build"), 0)

    def test_rm_rf_next_allowed(self):
        self.assertEqual(self.call("rm -rf .next && next build"), 0)

    def test_rm_rf_pycache_allowed(self):
        self.assertEqual(self.call("rm -rf __pycache__"), 0)

    def test_ls_untouched(self):
        self.assertEqual(self.call("ls -la"), 0)

    def test_safe_targets_disabled_blocks(self):
        os.environ["HOOK_ALLOW_SAFE_RM_TARGETS"] = "0"
        self.assertEqual(self.call("rm -rf node_modules"), 2)

    # ---------- SQL: blocked ----------
    def test_drop_table_mysql(self):
        self.assertEqual(self.call("mysql -e 'DROP TABLE users'"), 2)

    def test_drop_table_if_exists(self):
        self.assertEqual(self.call("psql -c 'drop table if exists users'"), 2)

    def test_truncate_table(self):
        self.assertEqual(self.call("mysql -e 'TRUNCATE users'"), 2)

    def test_truncate_with_keyword(self):
        self.assertEqual(self.call("mysql -e 'TRUNCATE TABLE users'"), 2)

    def test_delete_from_no_where(self):
        self.assertEqual(self.call("mysql -e 'DELETE FROM users'"), 2)

    def test_delete_from_sqlite(self):
        self.assertEqual(self.call("sqlite3 app.db 'DELETE FROM logs;'"), 2)

    def test_echo_drop_table_blocked_conservative(self):
        self.assertEqual(self.call('echo "DROP TABLE x"'), 2)

    def test_delete_in_chain(self):
        self.assertEqual(self.call("mysql -e 'delete from t' && echo done"), 2)

    def test_two_sql_rules(self):
        self.assertEqual(self.call("psql -c 'DROP TABLE a; DELETE FROM b'"), 2)
        rules = sorted(l["rule"] for l in self.log_lines())
        self.assertEqual(rules, ["delete-no-where", "drop-table"])

    # ---------- SQL: allowed ----------
    def test_delete_with_where_allowed(self):
        self.assertEqual(self.call("mysql -e 'DELETE FROM users WHERE id = 1'"), 0)

    def test_select_allowed(self):
        self.assertEqual(self.call("mysql -e 'SELECT * FROM users'"), 0)

    def test_drop_index_allowed(self):
        self.assertEqual(self.call("mysql -e 'DROP INDEX idx ON users'"), 0)

    def test_update_allowed(self):
        self.assertEqual(self.call("mysql -e 'UPDATE users SET x = 1'"), 0)

    def test_npm_test_allowed(self):
        self.assertEqual(self.call("npm test"), 0)

    def test_git_commit_allowed(self):
        self.assertEqual(self.call("git commit -m 'wip'"), 0)

    # ---------- git push --force ----------
    def test_push_force_long(self):
        self.assertEqual(self.call("git push --force"), 2)

    def test_push_force_short(self):
        self.assertEqual(self.call("git push -f origin main"), 2)

    def test_push_force_with_ref(self):
        self.assertEqual(self.call("git push --force origin main"), 2)

    def test_push_combined_short_flags(self):
        self.assertEqual(self.call("git push -uf origin main"), 2)

    def test_push_force_in_chain(self):
        self.assertEqual(self.call("cd repo && git push --force"), 2)

    def test_push_force_with_lease_allowed(self):
        self.assertEqual(self.call("git push --force-with-lease"), 0)

    def test_push_plain_allowed(self):
        self.assertEqual(self.call("git push"), 0)

    def test_push_upstream_allowed(self):
        self.assertEqual(self.call("git push -u origin main"), 0)

    # ---------- passthrough ----------
    def test_non_bash_tool_ignored(self):
        self.assertEqual(self.call("rm -rf /", tool="Write"), 0)
        self.assertEqual(self.log_lines(), [])

    def test_empty_command(self):
        self.assertEqual(self.call("   "), 0)

    def test_missing_tool_input(self):
        with redirect_stderr(self.err):
            self.assertEqual(g.run({"tool_name": "Bash"}), 0)

    def test_benign_no_log_file(self):
        self.assertEqual(self.call("ls -la"), 0)
        self.assertEqual(self.log_lines(), [])

    def test_echo_hello(self):
        self.assertEqual(self.call("echo hello world"), 0)

    # ---------- logging ----------
    def test_log_fields(self):
        self.call("rm -rf /")
        (line,) = self.log_lines()
        self.assertEqual(line["command"], "rm -rf /")
        self.assertEqual(line["cwd"], "/project")
        self.assertEqual(line["rule"], "rm-rf")
        self.assertEqual(line["segment"], "rm -rf /")
        self.assertIn("ts", line)

    def test_disable_rule(self):
        os.environ["HOOK_DISABLE_RULES"] = "rm-rf"
        self.assertEqual(self.call("rm -rf /"), 0)

    def test_stdout_decision_json(self):
        self.assertEqual(self.call("rm -rf /"), 2)
        self.assertEqual(json.loads(self.stdout_json)["decision"], "block")
        self.assertIn("rm-rf", self.stdout_json)

    def test_stderr_message(self):
        self.assertEqual(self.call("git push --force"), 2)
        self.assertIn("git-push-force", self.err.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
