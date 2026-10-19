import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location('guard', ROOT / 'pre_tool_use.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def test_blocked_commands(self):
        for command in ['rm -rf /tmp/x', 'sudo /bin/rm -f -R /tmp/x', 'rm --recursive --force x', 'git -C repo push origin -f', 'git push --force origin main', 'bash -c "rm -rf x"', 'psql -c "DROP TABLE users"', 'sqlite3 db "TRUNCATE TABLE users"', "psql -c 'DELETE FROM users'", 'psql -c "DELETE FROM users; SELECT 1 WHERE true"', 'psql -c "DELETE FROM users /* WHERE id=1 */"', 'psql -c "DELETE FROM users RETURNING \'WHERE\'"']:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.reason(command))

    def test_normal_commands(self):
        for command in ['ls -la', 'git status', 'git push origin main', 'git push --force-with-lease origin main', 'rm file.txt', 'rm -r folder', 'echo hello', 'psql -c "DELETE FROM users WHERE id=1"']:
            with self.subTest(command=command):
                self.assertIsNone(guard.reason(command))

    def test_protocol_and_log(self):
        with tempfile.TemporaryDirectory() as home:
            env = dict(os.environ, HOME=home, USERPROFILE=home)
            data = {'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf café'}, 'cwd': '/repo with spaces'}
            result = subprocess.run([sys.executable, str(ROOT / 'pre_tool_use.py')], input=json.dumps(data), text=True, capture_output=True, env=env)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')
            record = json.loads((pathlib.Path(home) / '.claude/hooks/blocked.log').read_text(encoding='utf-8'))
            self.assertEqual(record['command'], data['tool_input']['command'])
            self.assertEqual(record['project_path'], data['cwd'])
            self.assertIn('+00:00', record['timestamp'])

    def test_allow_has_no_permission_override(self):
        result = subprocess.run([sys.executable, str(ROOT / 'pre_tool_use.py')], input=json.dumps({'tool_name': 'Bash', 'tool_input': {'command': 'git status'}}), text=True, capture_output=True)
        self.assertEqual(result.stdout, '')

    def test_invalid_input_denied(self):
        result = subprocess.run([sys.executable, str(ROOT / 'pre_tool_use.py')], input='invalid', text=True, capture_output=True)
        self.assertEqual(json.loads(result.stdout)['hookSpecificOutput']['permissionDecision'], 'deny')


if __name__ == '__main__':
    unittest.main()
