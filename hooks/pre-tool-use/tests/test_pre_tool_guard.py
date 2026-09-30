import unittest, os, json, io, sys, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'hooks'))
from pre_tool_guard import check_command, main

class TestCheckCommand(unittest.TestCase):
    def test_rm_rf(self):
        self.assertIsNotNone(check_command("rm -rf /"))
    def test_rm_fr(self):
        self.assertIsNotNone(check_command("rm -fr /"))
    def test_rm_r_f(self):
        self.assertIsNotNone(check_command("rm -r -f /"))
    def test_rm_long_flags(self):
        self.assertIsNotNone(check_command("rm --recursive --force /"))
    def test_echo_rm_rf_allowed(self):
        self.assertIsNone(check_command("echo rm -rf is dangerous"))
    def test_git_push_force(self):
        self.assertIsNotNone(check_command("git push --force origin main"))
    def test_git_push_f(self):
        self.assertIsNotNone(check_command("git push -f origin main"))
    def test_git_push_force_with_lease_allowed(self):
        self.assertIsNone(check_command("git push --force-with-lease origin main"))
    def test_sql_drop_table(self):
        self.assertIsNotNone(check_command("mysql -c 'DROP TABLE users'"))
    def test_sql_truncate(self):
        self.assertIsNotNone(check_command("psql -e \"TRUNCATE logs\""))
    def test_sql_delete_no_where(self):
        self.assertIsNotNone(check_command("sqlite3 db.sqlite -c 'DELETE FROM items'"))
    def test_sql_delete_with_where_allowed(self):
        self.assertIsNone(check_command("sqlite3 db.sqlite -c 'DELETE FROM items WHERE id=1'"))
    def test_printf_drop_table_allowed(self):
        self.assertIsNone(check_command("printf 'DROP TABLE users'"))
    def test_bash_c_rm_rf(self):
        self.assertIsNotNone(check_command("bash -c 'rm -rf /tmp/test'"))
    def test_sh_c_git_push_force(self):
        self.assertIsNotNone(check_command("sh -c \"git push --force\""))
    def test_chain_semicolon(self):
        self.assertIsNotNone(check_command("echo ok; rm -rf /tmp/test"))
    def test_chain_and(self):
        self.assertIsNotNone(check_command("echo ok && rm -rf /tmp/test"))
    def test_newline_chain(self):
        self.assertIsNotNone(check_command("echo ok\nrm -rf /tmp/test"))
    def test_quoted_dangerous_text_allowed(self):
        self.assertIsNone(check_command("echo \"git push --force\""))
    def test_sudo_rm(self):
        self.assertIsNotNone(check_command("sudo rm -rf /tmp/test"))
    def test_env_echo_text_allowed(self):
        self.assertIsNone(check_command("env X=1 echo rm -rf /tmp/test"))
    def test_command_substitution(self):
        self.assertIsNotNone(check_command("echo $(rm -rf /tmp/test)"))
    def test_backtick_substitution(self):
        self.assertIsNotNone(check_command("echo `rm -rf /tmp/test`"))
    def test_safe_ls(self):
        self.assertIsNone(check_command("ls -la"))
    def test_case_insensitive_sql(self):
        self.assertIsNotNone(check_command("mysql -c 'drop table users'"))

class TestMain(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.home_patch = os.environ.get('HOME')
        os.environ['HOME'] = self.tmpdir
    def tearDown(self):
        if self.home_patch is not None:
            os.environ['HOME'] = self.home_patch
        shutil.rmtree(self.tmpdir)
    def _run_main(self, payload_str):
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        sys.stdin = io.StringIO(payload_str)
        sys.stdout = io.StringIO()
        try:
            rc = main()
            out = sys.stdout.getvalue()
        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout
        return rc, out
    def test_block_rm_rf(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}, "cwd": "/proj"})
        rc, out = self._run_main(payload)
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["hookSpecificOutput"]["permissionDecision"], "deny")
        log_path = os.path.join(self.tmpdir, '.claude', 'hooks', 'blocked.log')
        self.assertTrue(os.path.exists(log_path))
    def test_allow_safe(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        rc, out = self._run_main(payload)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")
    def test_non_bash_allowed(self):
        payload = json.dumps({"tool_name": "Read", "tool_input": {"path": "/a"}})
        rc, out = self._run_main(payload)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")
    def test_malformed_json_fails_open(self):
        rc, out = self._run_main("{bad json")
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")
    def test_missing_command_fails_open(self):
        payload = json.dumps({"tool_name": "Bash", "tool_input": {}})
        rc, out = self._run_main(payload)
        self.assertEqual(rc, 0)
        self.assertEqual(out.strip(), "")

if __name__ == '__main__':
    unittest.main()
