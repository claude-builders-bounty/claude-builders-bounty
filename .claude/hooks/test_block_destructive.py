import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('block-destructive.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
installer_spec = importlib.util.spec_from_file_location('installer', Path(__file__).with_name('install-block-destructive.py'))
installer = importlib.util.module_from_spec(installer_spec)
installer_spec.loader.exec_module(installer)

class GuardTests(unittest.TestCase):
    def test_required_and_equivalent_destructive_commands(self):
        commands = ['rm -rf /tmp/a', 'rm -r -f /tmp/a', 'rm --recursive --force /tmp/a',
            'rm -Rf /tmp/a', 'sudo rm -rf /tmp/a', 'echo ok; rm -rf /tmp/a',
            'echo ok\nrm -rf /tmp/a', 'bash -c "rm -r -f /tmp/a"',
            'DROP TABLE users;', 'TRUNCATE TABLE sessions;', 'DELETE FROM users;',
            'git push --force origin main', 'git -C /tmp/repo push --force-with-lease=refs/heads/main',
            'git push origin +main', 'git push -vf origin main', 'DELETE /* comment */ FROM users;',
            'sqlite3 test.db "DELETE FROM users /* WHERE id=1 */;"',
            'sqlite3 test.db "DELETE FROM users -- WHERE id=1"',
            'echo "DELETE FROM users;" | sqlite3 test.db']
        for command in commands:
            with self.subTest(command=command): self.assertIsNotNone(guard.blocked_reason(command))

    def test_safe_commands_including_quoted_documentation(self):
        for command in ['rm file.txt', 'git push origin feature', 'npm test',
            'echo "rm -rf /tmp/a"', 'echo "DROP TABLE users"',
            'grep "TRUNCATE" docs.md', 'DELETE FROM users WHERE id = 42;',
            'sqlite3 test.db "DELETE FROM users WHERE id=42;"',
            'rm -- -rf', 'SELECT * FROM users;']:
            with self.subTest(command=command): self.assertIsNone(guard.blocked_reason(command))

    def call(self, payload, failure=None):
        out = io.StringIO()
        with patch('sys.stdin', io.StringIO(payload)), patch.object(guard, 'log_block', side_effect=failure) as log, contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(guard.main(), 0)
        return out.getvalue(), log

    def test_json_denial_and_log_fields(self):
        out, log = self.call(json.dumps({'tool_name':'Bash','tool_input':{'command':'rm -rf /tmp/a'},'cwd':'/project'}))
        result = json.loads(out)['hookSpecificOutput']
        self.assertEqual(result['hookEventName'], 'PreToolUse')
        self.assertEqual(result['permissionDecision'], 'deny')
        self.assertEqual(log.call_args.args[:2], ('rm -rf /tmp/a', '/project'))

    def test_logging_failure_still_denies(self):
        out, _ = self.call(json.dumps({'tool_name':'Bash','tool_input':{'command':'rm -rf /tmp/a'}}), OSError('denied'))
        self.assertEqual(json.loads(out)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_malformed_input_denies(self):
        for payload in ['{bad', '[]', '{"tool_name":"Bash", "tool_input":null}']:
            out, _ = self.call(payload)
            self.assertEqual(json.loads(out)['hookSpecificOutput']['permissionDecision'], 'deny')

    def test_safe_input_emits_no_permission_override(self):
        out, log = self.call(json.dumps({'tool_name':'Bash','tool_input':{'command':'npm test'}}))
        self.assertEqual(out, '')
        log.assert_not_called()

    def test_installer_preserves_settings_and_is_idempotent(self):
        initial = {'permissions': {'deny': ['Read(.env)']}, 'hooks': {'PostToolUse': []}}
        updated = installer.updated_settings(initial, 'python3 /example/guard.py')
        self.assertEqual(initial, {'permissions': {'deny': ['Read(.env)']}, 'hooks': {'PostToolUse': []}})
        self.assertEqual(updated['permissions'], initial['permissions'])
        self.assertEqual(updated['hooks']['PostToolUse'], [])
        self.assertEqual(installer.updated_settings(updated, 'python3 /example/guard.py'), updated)

    def test_installer_rejects_invalid_configuration(self):
        for value in [[], {'hooks': []}, {'hooks': {'PreToolUse': {}}}, {'hooks': {'PreToolUse': [None]}}]:
            with self.assertRaises(ValueError): installer.updated_settings(value, 'python3 /example/guard.py')

if __name__ == '__main__': unittest.main()
