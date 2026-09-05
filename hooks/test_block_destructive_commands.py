import unittest
import sys, os
from pathlib import Path
sys.path.insert(0, os.path.abspath('bounties/GH-3'))
from block_destructive_commands import check_command_safety

class TestBlockDestructiveCommands(unittest.TestCase):
    def test_blocks_rm_rf(self):
        for cmd in ['rm -rf /tmp/data', 'rm -fr /', 'rm -r -f node_modules']:
            safe, reason = check_command_safety(cmd)
            self.assertFalse(safe, f'Expected {cmd} to be blocked')
            self.assertIn('rm -rf', reason)

    def test_blocks_drop_table(self):
        safe, reason = check_command_safety('DROP TABLE accounts;')
        self.assertFalse(safe)
        self.assertIn('DROP TABLE', reason)

    def test_blocks_git_force_push(self):
        for cmd in ['git push origin main --force', 'git push -f origin feat']:
            safe, reason = check_command_safety(cmd)
            self.assertFalse(safe)
            self.assertIn('force', reason)

    def test_blocks_truncate(self):
        for cmd in ['TRUNCATE TABLE session_cache;', 'truncate users']:
            safe, reason = check_command_safety(cmd)
            self.assertFalse(safe)
            self.assertIn('TRUNCATE', reason)

    def test_blocks_delete_without_where(self):
        for cmd in ['DELETE FROM users;', 'delete from accounts']:
            safe, reason = check_command_safety(cmd)
            self.assertFalse(safe)
            self.assertIn('DELETE FROM without a WHERE', reason)

    def test_allows_safe_commands(self):
        safe_cmds = [
            'rm file.txt',
            'git push origin feature-branch',
            'SELECT * FROM users;',
            'DELETE FROM users WHERE id = 42;',
            'npm run build',
            'pytest tests/'
        ]
        for cmd in safe_cmds:
            safe, reason = check_command_safety(cmd)
            self.assertTrue(safe, f'Expected {cmd} to be allowed, got: {reason}')

if __name__ == '__main__':
    unittest.main()
