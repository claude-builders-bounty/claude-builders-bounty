import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch
import hook

class GuardTests(unittest.TestCase):
    def test_dangerous(self):
        for command in ['rm -rf /tmp/a', 'rm -fr /tmp/a', 'rm -r --force /tmp/a', 'rm --force -r /tmp/a', 'rm --recursive -f /tmp/a', 'DELETE FROM users /* WHERE */', 'rm --recursive --force /tmp/a', 'DROP TABLE users', 'TRUNCATE TABLE users', 'git push origin main --force', 'git push -f origin main', 'DELETE FROM users;']:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.check(command))

    def test_safe(self):
        for command in ['rm -i a', 'git push origin main', 'SELECT * FROM users', 'DELETE FROM users WHERE id=1', 'echo hello', 'git status']:
            with self.subTest(command=command):
                self.assertIsNone(hook.check(command))

    def test_block_and_log(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {'tool_name': 'Bash', 'tool_input': {'command': 'DROP TABLE users'}, 'cwd': '/example'}
            with patch.dict(os.environ, {'HOME': home}), patch('sys.stdin', io.StringIO(json.dumps(payload))), redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(hook.main(), 2)
            log = Path(home) / '.claude/hooks/blocked.log'
            self.assertTrue(log.exists())
            record = json.loads(log.read_text().strip())
            self.assertEqual(record['project_path'], '/example')
            self.assertEqual(len(log.read_text().splitlines()), 1)
            self.assertIn('DROP TABLE', stderr.getvalue())

    def test_allow_no_log(self):
        with tempfile.TemporaryDirectory() as home:
            payload = {'tool_name': 'Bash', 'tool_input': {'command': 'git status'}}
            with patch.dict(os.environ, {'HOME': home}), patch('sys.stdin', io.StringIO(json.dumps(payload))):
                self.assertEqual(hook.main(), 0)
            self.assertFalse((Path(home) / '.claude/hooks/blocked.log').exists())

    def test_malformed_denied(self):
        with patch('sys.stdin', io.StringIO('{bad')), redirect_stderr(io.StringIO()):
            self.assertEqual(hook.main(), 2)

if __name__ == '__main__':
    unittest.main()
