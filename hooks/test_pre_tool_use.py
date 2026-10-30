import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HOOK = Path(__file__).with_name('pre-tool-use.py')


class HookTests(unittest.TestCase):
    def test_official_payload_blocks_and_logs_each_required_pattern(self):
        commands = ['rm -rf /example', 'rm -fr /example', 'git push --force',
                    'git push origin main -f', 'DROP TABLE users;',
                    'TRUNCATE users;', 'DELETE FROM users;']
        with tempfile.TemporaryDirectory() as directory:
            for command in commands:
                with self.subTest(command=command):
                    # Import in a child process while redirecting only the test log.
                    bootstrap = (
                        "import runpy; "
                        f"g=runpy.run_path({str(HOOK)!r}); "
                        f"g['main'].__globals__['LOG_DIR']={directory!r}; "
                        f"g['main'].__globals__['LOG_FILE']={str(Path(directory) / 'blocked.log')!r}; "
                        "g['main']()"
                    )
                    payload = {'tool_name': 'Bash', 'tool_input': {'command': command},
                               'cwd': '/project-under-review'}
                    result = subprocess.run([sys.executable, '-c', bootstrap],
                                            input=json.dumps(payload), text=True,
                                            encoding='utf-8', capture_output=True)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn('blocked a destructive command', result.stderr)
                    log = (Path(directory) / 'blocked.log').read_text(encoding='utf-8')
                    self.assertIn(command, log)
                    self.assertIn('/project-under-review', log)

    def test_safe_bash_and_non_bash_tools_are_allowed(self):
        for tool, command in [('Bash', 'git status'), ('Bash', 'SELECT * FROM users'),
                              ('Bash', 'DELETE FROM users WHERE id = 1;'),
                              ('Read', 'rm -rf /example')]:
            with self.subTest(tool=tool, command=command):
                result = subprocess.run([sys.executable, str(HOOK)],
                    input=json.dumps({'tool_name': tool, 'tool_input': {'command': command}}),
                    text=True, encoding='utf-8', capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_installer_preserves_settings_and_is_idempotent(self):
        spec = importlib.util.spec_from_file_location('installer', HOOK.with_name('install.py'))
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {'permissions': {'allow': ['Read']}, 'hooks': {'Stop': []}}
            (root / 'settings.json').write_text(json.dumps(original))
            installer.install(root)
            installer.install(root)
            settings = json.loads((root / 'settings.json').read_text())
            self.assertEqual(settings['permissions'], original['permissions'])
            self.assertEqual(settings['hooks']['Stop'], [])
            self.assertEqual(len(settings['hooks']['PreToolUse']), 1)
            self.assertEqual((root / 'hooks/pre-tool-use.py').read_bytes(), HOOK.read_bytes())


if __name__ == '__main__':
    unittest.main()
