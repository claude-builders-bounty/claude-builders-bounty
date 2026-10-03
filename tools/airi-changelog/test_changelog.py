import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from changelog import generate


class GitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.commit('chore: initial')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def commit(self, message):
        self.git('commit', '--allow-empty', '-qm', message)

    def test_tagged_categories(self):
        self.git('tag', 'v1')
        for message in ['feat(api): add endpoint', 'fix: repair timeout', 'docs: update guide', 'remove: obsolete flag']:
            self.commit(message)
        text, baseline, count = generate(self.repo)
        self.assertEqual((baseline, count), ('v1', 4))
        for category in ['Added', 'Fixed', 'Changed', 'Removed']:
            self.assertIn('### ' + category, text)
        self.assertNotIn('initial', text)

    def test_no_tags_and_escape(self):
        self.commit('feat: <script> [bad](url) *text*')
        text, baseline, count = generate(self.repo)
        self.assertEqual((baseline, count), (None, 2))
        self.assertIn('&lt;script&gt;', text)
        self.assertIn('\\[bad\\]', text)

    def test_no_changes(self):
        self.git('tag', 'v1')
        self.assertIn('No changes', generate(self.repo)[0])

    def test_unusual_subjects(self):
        self.git('tag', 'v1_beta')
        for subject in ['Added support', 'Fixed bug', 'Removed option', 'Note: preserve prefix', 'feat:', 'feat: unicode\u2028separator']:
            self.commit(subject)
        text, baseline, count = generate(self.repo, 'v1_beta')
        self.assertEqual(count, 6)
        self.assertIn('Note: preserve prefix', text)
        self.assertIn('feat:', text)
        self.assertIn('unicode\u2028separator', text)

    def test_force(self):
        output = self.repo / 'CHANGELOG.md'
        output.write_text('old')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('changelog.py')),
                                 '--repo', str(self.repo), '--output', str(output), '--force'], capture_output=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn('# Changelog', output.read_text())

    def test_invalid_ref(self):
        with self.assertRaises(ValueError):
            generate(self.repo, '--all')

    def test_shallow(self):
        (self.repo / '.git' / 'shallow').write_text(self.git('rev-parse', 'HEAD') + '\n')
        with self.assertRaisesRegex(ValueError, 'Shallow'):
            generate(self.repo)

    def test_preserves_existing_file(self):
        output = self.repo / 'CHANGELOG.md'
        output.write_text('keep')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('changelog.py')),
                                 '--repo', str(self.repo), '--output', str(output)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
