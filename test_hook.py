#!/usr/bin/env python3
"""Zero-dependency integration and regression tests."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
HOOK = ROOT / 'hooks' / 'block-destructive-bash.py'

class HookTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.log = Path(self.tmp.name) / 'blocked.log'

    def run_hook(self, command, *, tool='Bash', cwd='/work/sample-project'):
        env = {**os.environ, 'CLAUDE_HOOK_LOG': str(self.log)}
        payload = {'tool_name': tool, 'cwd': cwd, 'tool_input': {'command': command}}
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), text=True, capture_output=True, env=env)

    def test_dangerous_commands_blocked(self):
        dangerous = [
            'rm -rf /tmp/demo', 'rm -fr /tmp/demo', 'rm --force --recursive /tmp/demo',
            'sudo rm -r -f /tmp/demo', 'echo safe && rm -rf /tmp/demo',
            'git push --force origin main', 'git push -f origin main',
            'git -C /tmp/myrepo push --force origin main',
            'git reset --hard HEAD~1', 'git checkout -- important.txt',
            'DROP TABLE users', 'TRUNCATE TABLE users', 'DELETE FROM users',
            'psql -c "DROP TABLE users;"', 'mysql -e "DELETE FROM customers;"',
            'sqlite3 db.sqlite "TRUNCATE TABLE users"', 'bash -c "rm -rf /tmp/demo"',
            'chmod 777 secrets',
        ]
        for cmd in dangerous:
            with self.subTest(cmd=cmd):
                got = self.run_hook(cmd)
                self.assertEqual(got.returncode, 2, (cmd, got.stderr))
                self.assertIn('BLOCKED', got.stderr)
        logs = [json.loads(line) for line in self.log.read_text(encoding='utf-8').splitlines()]
        self.assertEqual(len(logs), len(dangerous))
        self.assertTrue(all(entry.get('project_path') == '/work/sample-project' for entry in logs))
        self.assertTrue(all(entry.get('timestamp') and entry.get('command') and entry.get('reason') for entry in logs))

    def test_ordinary_commands_allowed(self):
        safe = ['echo hello', 'echo "rm -rf /tmp"', 'printf "DROP TABLE users"',
                'git push origin main', 'git push --force-with-lease origin main',
                'rm -r ./tmp', 'rm -f ./file', 'chmod 755 file',
                'DELETE FROM users WHERE id = 1', 'psql -c "DELETE FROM users WHERE id=1"',
                'ls -la && echo OK', 'bash -c "echo rm -rf safe"']
        for cmd in safe:
            with self.subTest(cmd=cmd):
                got = self.run_hook(cmd)
                self.assertEqual(got.returncode, 0, (cmd, got.stderr))
        self.assertFalse(self.log.exists())

    def test_ignores_other_tools_or_malformed_payloads(self):
        got = self.run_hook('rm -rf /tmp/demo', tool='Read')
        self.assertEqual(got.returncode, 0)
        raw = subprocess.run([sys.executable, str(HOOK)], input='bad-json', text=True, capture_output=True)
        self.assertEqual(raw.returncode, 0)

    def test_one_command_installer_preserves_settings_and_is_idempotent(self):
        home = Path(self.tmp.name) / 'home'
        home.mkdir()
        settings = home / '.claude' / 'settings.json'
        settings.parent.mkdir()
        settings.write_text(json.dumps({'model': 'sonnet', 'hooks': {'PreToolUse': [{'matcher': 'Read', 'hooks': [{'type': 'command', 'command': 'echo before'}]}]}}))
        env = {**os.environ, 'HOME': str(home)}
        for _ in range(2):
            got = subprocess.run(['bash', str(ROOT / 'install.sh')], text=True, capture_output=True, env=env)
            self.assertEqual(got.returncode, 0, got.stderr)
        installed = json.loads(settings.read_text())
        self.assertEqual(installed['model'], 'sonnet')
        self.assertEqual(len(installed['hooks']['PreToolUse']), 2)
        self.assertTrue((home / '.claude' / 'hooks' / 'block-destructive-bash.py').exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
