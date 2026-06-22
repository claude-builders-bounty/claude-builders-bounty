import unittest, sys; sys.path.insert(0, 'hooks')
from block_destructive_bash import check_command, PATTERNS

class TestHook(unittest.TestCase):
    def test_block_rm_rf(self):
        b, i = check_command("rm -rf /", PATTERNS); self.assertTrue(b)
    def test_block_drop_table(self):
        b, i = check_command("DROP TABLE users", PATTERNS); self.assertTrue(b)
    def test_block_git_force(self):
        b, i = check_command("git push -f", PATTERNS); self.assertTrue(b)
    def test_block_delete(self):
        b, i = check_command("DELETE FROM users", PATTERNS); self.assertTrue(b)
    def test_allow_ls(self):
        b, i = check_command("ls -la", PATTERNS); self.assertFalse(b)
    def test_allow_git_status(self):
        b, i = check_command("git status", PATTERNS); self.assertFalse(b)
    def test_allow_rm_file(self):
        b, i = check_command("rm file.txt", PATTERNS); self.assertFalse(b)
    def test_allow_delete_where(self):
        b, i = check_command("DELETE FROM users WHERE id=1", PATTERNS); self.assertFalse(b)
    def test_case_insensitive_sql(self):
        b, i = check_command("drop table users", PATTERNS); self.assertTrue(b)

if __name__ == "__main__": unittest.main()
