#!/usr/bin/env python3
import sys
import os
import unittest

# Add hook directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../hooks')))

from destructive_command_hook import (
    check_rm_rf,
    check_drop_table,
    check_git_push_force,
    check_truncate,
    check_delete_without_where,
    is_safe_command_prefix,
    is_destructive
)

class TestDestructiveCommandHook(unittest.TestCase):
    
    def test_rm_rf(self):
        # Destructive
        self.assertIsNotNone(is_destructive("rm -rf /"))
        self.assertIsNotNone(is_destructive("rm -fr /"))
        self.assertIsNotNone(is_destructive("rm -r -f /"))
        self.assertIsNotNone(is_destructive("rm -f -r /"))
        self.assertIsNotNone(is_destructive("rm -rfv /"))
        self.assertIsNotNone(is_destructive("rm --recursive --force /"))
        
        # Safe/Normal
        self.assertIsNone(is_destructive("rm -f file.txt"))
        self.assertIsNone(is_destructive("rm -r dir/"))
        self.assertIsNone(is_destructive("rmdir empty_dir"))
    
    def test_drop_table(self):
        # Destructive
        self.assertIsNotNone(is_destructive("DROP TABLE users"))
        self.assertIsNotNone(is_destructive("drop table logs"))
        self.assertIsNotNone(is_destructive("sqlite3 db.sqlite 'DROP TABLE users;'"))
        
        # Safe/Normal
        self.assertIsNone(is_destructive("echo 'DROP TABLE'"))
    
    def test_git_push_force(self):
        # Destructive
        self.assertIsNotNone(is_destructive("git push --force origin main"))
        self.assertIsNotNone(is_destructive("git push -f origin main"))
        self.assertIsNotNone(is_destructive("git push origin main --force"))
        
        # Safe/Normal
        self.assertIsNone(is_destructive("git push origin main"))
        self.assertIsNone(is_destructive("git pull origin main"))
    
    def test_truncate(self):
        # Destructive
        self.assertIsNotNone(is_destructive("TRUNCATE users"))
        self.assertIsNotNone(is_destructive("truncate table logs"))
        
        # Safe/Normal
        self.assertIsNone(is_destructive("echo 'truncate'"))
        self.assertIsNone(is_destructive("truncated_name"))
        
    def test_delete_without_where(self):
        # Destructive
        self.assertIsNotNone(is_destructive("DELETE FROM users"))
        self.assertIsNotNone(is_destructive("delete from logs;"))
        self.assertIsNotNone(is_destructive("delete from users; delete from logs where id=1"))
        
        # Safe/Normal
        self.assertIsNone(is_destructive("DELETE FROM users WHERE id = 1"))
        self.assertIsNone(is_destructive("delete from logs where name='test'"))
        
    def test_safe_prefix(self):
        # Safe
        self.assertTrue(is_safe_command_prefix("echo 'DROP TABLE users'"))
        self.assertTrue(is_safe_command_prefix("git diff"))
        self.assertTrue(is_safe_command_prefix("git show HEAD"))
        
        # Dangerous/unsafe (has pipe or redirect)
        self.assertFalse(is_safe_command_prefix("echo 'DROP TABLE users' | sqlite3 db.sqlite"))
        self.assertFalse(is_safe_command_prefix("cat schema.sql > db.sqlite"))

if __name__ == '__main__':
    unittest.main()
