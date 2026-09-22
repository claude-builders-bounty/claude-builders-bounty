import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import guard
import install


class GuardTests(unittest.TestCase):
    def test_dangerous_commands(self):
        commands = [
            'rm -rf ./build', '/bin/rm -fr ./build', 'sudo rm -r -f ./build',
            'env MODE=test rm --recursive --force ./build', 'rm -Rf ./build',
            'echo ready; rm -rf ./build', 'true && rm -rf ./build',
            'echo ready\nrm -rf ./build', 'rm -r\\\n -f ./build',
            "bash -lc 'rm -rf ./build'", 'git push --force origin main',
            'git -C project push -f', 'git push origin +main',
            'git push --force-with-lease origin main',
            'psql -c "DROP TABLE users"', 'sqlite3 db "TRUNCATE users"',
            'mysql -e "DELETE FROM users"',
            'psql -c "DELETE FROM users; SELECT 1 WHERE true"',
            "psql -c \"DELETE FROM users RETURNING 'WHERE'\"",
            'psql -c "DELETE FROM users /* WHERE id = 1 */"',
            'psql -c "DELETE FROM users RETURNING (SELECT id FROM x WHERE true)"',
            'psql -c "DROP/**/TABLE users"',
            "echo 'DELETE FROM users' | sqlite3 db",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.shell_reason(command))

    def test_normal_commands(self):
        commands = [
            'git status', 'git push origin main', 'git log --oneline',
            'python -m unittest', 'npm test', 'ls -la', 'rm file.txt',
            'rm -r build', 'rm -f file.txt', 'rm -- -rf',
            "echo 'rm -rf build'", "printf '%s' 'DROP TABLE users'",
            "rg 'DELETE FROM' src", 'command -v rm',
            'psql -c "SELECT 1"', 'psql -c "DELETE FROM users WHERE id = 1"',
            "psql -c \"SELECT 'DROP TABLE users'\"",
            'psql -c "-- DROP TABLE users\nSELECT 1"',
            'sqlite3 db "DELETE FROM users WHERE id=1; SELECT 1"',
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(guard.shell_reason(command))

    def run_hook(self, home, event):
        env = dict(os.environ, HOME=str(home), USERPROFILE=str(home))
        return subprocess.run([sys.executable, str(Path(guard.__file__))],
                              input=json.dumps(event), text=True, capture_output=True, env=env)

    def test_protocol_and_audit(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            event = {'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf example\n'},
                     'cwd': '/project with spaces'}
            result = self.run_hook(home, event)
            self.assertEqual(result.returncode, 2)
            self.assertIn('Recursive forced', result.stderr)
            self.assertEqual(result.stdout, '')
            records = (home / '.claude/hooks/blocked.log').read_text().splitlines()
            self.assertEqual(len(records), 1)
            record = json.loads(records[0])
            self.assertEqual(record['command'], event['tool_input']['command'])
            self.assertEqual(record['project_path'], event['cwd'])
            self.assertTrue(record['timestamp'].endswith('+00:00'))
            event['tool_input']['command'] = 'git status'
            result = self.run_hook(home, event)
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertEqual(len((home / '.claude/hooks/blocked.log').read_text().splitlines()), 1)

    def test_logging_failure_still_blocks(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / '.claude').write_text('obstruction')
            result = self.run_hook(home, {'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf x'}})
            self.assertEqual(result.returncode, 2)
            self.assertIn('Audit log unavailable', result.stderr)

    def test_invalid_input_and_other_tools(self):
        with tempfile.TemporaryDirectory() as temp:
            for event in [[], {'tool_name': 'Bash'}, {'tool_name': 'Bash', 'tool_input': {'command': 1}}]:
                self.assertEqual(self.run_hook(temp, event).returncode, 2)
            self.assertEqual(self.run_hook(temp, {'tool_name': 'Read'}).returncode, 0)
            self.assertIsNotNone(guard.shell_reason("rm 'unterminated"))

    def test_installer_preserves_settings_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as temp, patch('pathlib.Path.home', return_value=Path(temp)):
            folder = Path(temp) / '.claude'
            folder.mkdir()
            original = {'model': 'existing', 'hooks': {'PreToolUse': [{'matcher': 'Read', 'hooks': []}]}}
            path = folder / 'settings.json'
            path.write_text(json.dumps(original))
            install.install()
            first = path.read_bytes()
            install.install()
            self.assertEqual(path.read_bytes(), first)
            current = json.loads(first)
            self.assertEqual(current['model'], 'existing')
            self.assertEqual(current['hooks']['PreToolUse'][0], original['hooks']['PreToolUse'][0])
            self.assertEqual(len(current['hooks']['PreToolUse']), 2)
            self.assertEqual(json.loads((folder / 'settings.before-destructive-guard.json').read_text()), original)
            self.assertTrue((folder / 'hooks/destructive_guard.py').exists())


if __name__ == '__main__':
    unittest.main()
