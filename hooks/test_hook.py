import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).parent


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


hook = module('block_destructive')
installer = module('install')


class PolicyTests(unittest.TestCase):
    def test_blocked_commands(self):
        commands = [
            'rm -rf ./sample', 'rm -fr ./sample', '/bin/rm -r -f ./sample',
            'rm --recursive --force ./sample', 'sudo -u nobody rm -Rf ./sample',
            'env NAME=value command rm -rf ./sample', 'true && rm -rf ./sample',
            'for x in a; do rm -rf "$x"; done', 'echo "$(rm -rf ./sample)"',
            'echo `rm -rf ./sample`', "bash -lc 'rm -rf ./sample'",
            'git push --force origin main', 'git -C ./sample push -f origin main',
            'git push --force-with-lease origin main', 'git push origin +main',
            'DROP TABLE customers;', 'TRUNCATE TABLE customers;',
            'DELETE FROM customers;', 'DELETE FROM customers /* WHERE id=1 */;',
            "DELETE FROM customers -- WHERE id=1\n;",
            "DELETE FROM customers RETURNING 'WHERE';",
            'DELETE FROM customers RETURNING (SELECT id FROM other WHERE id=1);',
            'WITH x AS (SELECT id FROM other WHERE id=1) DELETE FROM customers;',
            "psql -c 'DELETE FROM customers;'", 'mysql --execute="DROP TABLE customers"',
            'mysql -e"TRUNCATE customers"', 'sqlite3 demo.db "DELETE FROM customers"',
            "psql -c 'DELETE FROM customers WHERE id=1; DELETE FROM other;'",
            "echo 'DROP TABLE customers' | psql",
            "printf '%s\\n' 'DROP TABLE customers;' | psql",
            'sudo -S rm -rf ./sample',
            "mysql <<'SQL'\nDELETE FROM customers /* WHERE */;\nSQL\n",
            "cat <<EOF\n$(rm -rf synthetic)\nEOF\n",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNotNone(hook.blocked_reason(command))

    def test_ordinary_commands(self):
        commands = [
            'ls -la', 'npm test', 'git status', 'git push origin main',
            'git push --force-if-includes origin main', 'rm -r ./sample',
            'rm -f sample.txt', 'rm -- -rf', "echo 'rm -rf sample'",
            "printf '%s' 'DROP TABLE customers'", "grep 'DELETE FROM' fixture.sql",
            "echo ';' rm -rf sample", "echo '$(rm -rf sample)'",
            'echo "a; DROP TABLE customers"', 'echo hello # rm -rf sample',
            'DELETE FROM customers WHERE id=1;',
            "psql -c \"DELETE FROM customers WHERE note='WHERE; TRUNCATE'\"",
            "psql -c 'SELECT 1; SELECT 2'", 'sqlite3 demo.db "SELECT 1"',
            'echo hello # $(rm -rf synthetic)',
            "echo 'DROP TABLE customers'; psql -c 'SELECT 1'",
            "printf '%s\\n' 'DROP TABLE customers;'",
            "cat <<'EOF'\nrm -rf synthetic\nDELETE FROM customers\nEOF\n",
            "mysql <<SQL\nDELETE FROM customers WHERE id=1;\nSQL\n",
            'echo hello # <<EOF',
            "cat \"it's\" <<'EOF'\nrm -rf synthetic\nEOF\n",
        ]
        for command in commands:
            with self.subTest(command=command):
                self.assertIsNone(hook.blocked_reason(command))


class ProtocolTests(unittest.TestCase):
    def run_hook(self, home, payload):
        env = os.environ | {'HOME': str(home), 'USERPROFILE': str(home)}
        # Windows expanduser derives the home from USERPROFILE; POSIX uses HOME.
        return subprocess.run([sys.executable, str(ROOT / 'block_destructive.py')],
                              input=payload, text=True, capture_output=True, env=env)

    def test_block_exit_message_and_jsonl_audit(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            event = {'hook_event_name': 'PreToolUse', 'tool_name': 'Bash',
                     'tool_input': {'command': 'rm -rf synthetic\n# log newline'},
                     'cwd': '/project with spaces'}
            for _ in range(2):
                result = self.run_hook(home, json.dumps(event))
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('Blocked:', result.stderr)
            records = (home / '.claude/hooks/blocked.log').read_text().splitlines()
            self.assertEqual(len(records), 2)
            record = json.loads(records[0])
            self.assertEqual(record['command'], event['tool_input']['command'])
            self.assertEqual(record['project_path'], event['cwd'])
            self.assertRegex(record['timestamp'], r'\+00:00$')

    def test_allowed_and_other_tools_do_not_log_or_grant_permission(self):
        with tempfile.TemporaryDirectory() as tmp:
            for event in [dict(tool_name='Bash', tool_input={'command': 'git status'}),
                          dict(tool_name='Read', tool_input={'command': 'rm -rf synthetic'})]:
                result = self.run_hook(Path(tmp), json.dumps(event))
                self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertFalse((Path(tmp) / '.claude').exists())

    def test_malformed_input_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            for payload in ['{', '[]', '{"tool_name":"Bash"}',
                            '{"tool_name":"Bash","tool_input":{"command":false}}']:
                result = self.run_hook(Path(tmp), payload)
                self.assertEqual(result.returncode, 2)

    def test_logging_failure_still_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / '.claude').write_text('not a directory')
            result = self.run_hook(home, json.dumps(dict(tool_name='Bash', tool_input={'command': 'rm -rf synthetic'})))
            self.assertEqual(result.returncode, 2)
            self.assertIn('Audit log could not be written', result.stderr)


class InstallerTests(unittest.TestCase):
    def test_merge_idempotence_backup_and_paths_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='hook home ') as tmp:
            home = Path(tmp)
            settings = home / '.claude/settings.json'
            settings.parent.mkdir()
            original = '{"permissions":{"deny":["Bash(curl *)"]},"hooks":{"PreToolUse":[{"matcher":"Read","hooks":[]}]}}'
            settings.write_text(original)
            target = installer.install(home)
            installer.install(home)
            merged = json.loads(settings.read_text())
            self.assertEqual(merged['permissions']['deny'], ['Bash(curl *)'])
            self.assertEqual(len(merged['hooks']['PreToolUse']), 2)
            self.assertEqual(merged['hooks']['PreToolUse'][1]['matcher'], 'Bash')
            self.assertEqual(settings.with_suffix('.json.before-destructive-hook').read_text(), original)
            self.assertEqual(target.read_bytes(), (ROOT / 'block_destructive.py').read_bytes())

    def test_invalid_settings_and_existing_script_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            settings = home / '.claude/settings.json'
            settings.parent.mkdir()
            settings.write_text('invalid json')
            with self.assertRaises(ValueError):
                installer.install(home)
            self.assertEqual(settings.read_text(), 'invalid json')
            settings.write_text('{}')
            target = home / '.claude/hooks/block_destructive.py'
            target.parent.mkdir()
            target.write_text('existing user hook')
            with self.assertRaises(ValueError):
                installer.install(home)
            self.assertEqual(target.read_text(), 'existing user hook')
            self.assertEqual(settings.read_text(), '{}')


if __name__ == '__main__':
    unittest.main()
