import contextlib
import io
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


BAD = [
    'rm -rf scratch', 'rm -fr scratch', 'rm -r -f scratch', '/bin/rm --recursive --force scratch',
    'sudo rm -Rf scratch', 'env X=1 rm -rf scratch', 'ls; rm -rf scratch',
    'echo ok\nrm -rf scratch', 'rm -r\\\n -f scratch', "bash -lc 'rm -rf scratch'",
    'git push --force origin main', 'git push -f origin main', 'git push -vf origin main',
    'git -C repo push --force-with-lease origin main', 'git push --force-with-lease=main origin main',
    'git push origin +main:main', 'git push --force-if-includes',
    'DROP TABLE users', 'TRUNCATE users', 'DELETE FROM users',
    'psql -c "DROP TABLE users"', 'mysql -e "TRUNCATE TABLE users"',
    'sqlite3 db "DELETE FROM users"', 'psql -c "DELETE FROM x; DELETE FROM y WHERE id=1"',
    "psql -c \"DELETE FROM x /* WHERE */\"", "psql -c \"DELETE FROM x RETURNING 'WHERE'\"",
    'psql -c "DELETE FROM x RETURNING (SELECT a FROM y WHERE b=1)"',
    "echo 'DROP TABLE users' | psql", 'rm "unterminated',
    "sqlite3 db 'DELETE FROM \"WHERE\"'", "sqlite3 db 'DELETE FROM x RETURNING \"WHERE\"'",
]
GOOD = [
    'ls -la', 'pwd', 'git status', 'git push origin main', 'git log --grep push -f',
    'rm file.txt', 'rm -r scratch', 'rm -f file.txt', 'rm -- -rf',
    'echo "rm -rf scratch"', "printf '%s' 'DROP TABLE x'", "grep 'DELETE FROM' README.md",
    'psql -c "SELECT 1"', 'psql -c "DELETE FROM x WHERE id=1"',
    'psql -c "SELECT \'DROP TABLE x\'"', 'psql -c "-- DROP TABLE x\nSELECT 1"',
    'psql -c "/* TRUNCATE x */ SELECT 1"', 'echo git push --force',
]


class GuardTests(unittest.TestCase):
    def test_protocol_and_log(self):
        with tempfile.TemporaryDirectory() as temp:
            env = dict(os.environ, HOME=temp, USERPROFILE=temp)
            payload = {'tool_name': 'Bash', 'tool_input': {'command': 'rm -rf dummy'}, 'cwd': '/sample/路径'}
            result = subprocess.run([sys.executable, str(Path(guard.__file__))], input=json.dumps(payload),
                                    text=True, capture_output=True, env=env, check=False)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stderr, '')
            output = json.loads(result.stdout)['hookSpecificOutput']
            self.assertEqual(output['hookEventName'], 'PreToolUse')
            self.assertEqual(output['permissionDecision'], 'deny')
            record = json.loads((Path(temp)/'.claude/hooks/blocked.log').read_text())
            self.assertEqual(record['command'], payload['tool_input']['command'])
            self.assertEqual(record['cwd'], payload['cwd'])
            self.assertIn('+00:00', record['timestamp'])

    def invoke(self, payload):
        output = io.StringIO()
        with patch('sys.stdin', io.StringIO(payload)), contextlib.redirect_stdout(output):
            self.assertEqual(guard.main(), 0)
        return output.getvalue()

    def test_allow_silent(self):
        self.assertEqual(self.invoke(json.dumps({'tool_name':'Bash','tool_input':{'command':'ls'}})), '')

    def test_other_tool_silent(self):
        self.assertEqual(self.invoke('{"tool_name":"Read"}'), '')

    def test_invalid_input_denied(self):
        for data in ['oops', '[]', '{"tool_name":"Bash"}', '{"tool_name":"Bash","tool_input":{"command":4}}']:
            self.assertEqual(json.loads(self.invoke(data))['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_log_failure_still_denies(self):
        with patch('pathlib.Path.mkdir', side_effect=PermissionError('test denied')):
            result = self.invoke('{"tool_name":"Bash","tool_input":{"command":"rm -rf dummy"}}')
        self.assertIn('audit log failed', json.loads(result)['hookSpecificOutput']['permissionDecisionReason'])

    def test_installer_preserves_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'.claude'
            root.mkdir()
            original = {'model':'existing','hooks':{'PreToolUse':[{'matcher':'Read','hooks':[]}]}}
            settings = root/'settings.json'
            settings.write_text(json.dumps(original))
            install.install(temp)
            first = settings.read_bytes()
            install.install(temp)
            self.assertEqual(first, settings.read_bytes())
            self.assertEqual(json.loads(first)['model'], 'existing')
            self.assertEqual(json.loads(first)['hooks']['PreToolUse'][0], original['hooks']['PreToolUse'][0])
            self.assertEqual(json.loads((root/'settings.json.before-destructive-guard').read_text()), original)

    def test_installer_rejects_invalid_json_without_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)/'.claude'
            root.mkdir()
            settings = root/'settings.json'
            settings.write_text('{broken')
            with self.assertRaises(ValueError):
                install.install(temp)
            self.assertEqual(settings.read_text(), '{broken')
            self.assertFalse((root/'hooks').exists())


def case(command, denied):
    def run(self):
        self.assertEqual(bool(guard.inspect(command)), denied, command)
    return run


for index, command in enumerate(BAD):
    setattr(GuardTests, 'test_block_%02d' % index, case(command, True))
for index, command in enumerate(GOOD):
    setattr(GuardTests, 'test_allow_%02d' % index, case(command, False))

if __name__ == '__main__':
    unittest.main()
