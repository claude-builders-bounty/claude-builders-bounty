import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'changelog.py'
spec = importlib.util.spec_from_file_location('changelog', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo with spaces'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')

    def git(self, *args):
        return module.git(self.repo, *args)

    def commit(self, subject):
        self.git('commit', '--allow-empty', '-qm', subject)

    def test_tag_boundary_all_categories_and_escaping(self):
        self.commit('feat: old release')
        self.git('tag', 'v1')
        for subject in ['feat(ui): add café', 'fix: quote `code` <script>', 'refactor!: new API', 'chore: remove legacy']:
            self.commit(subject)
        text, base, _ = module.generate(self.repo)
        self.assertEqual(base, 'v1')
        self.assertNotIn('old release', text)
        for category in module.CATEGORIES:
            self.assertIn('### ' + category, text)
        self.assertIn('café', text)
        self.assertIn('BREAKING: new API', text)
        self.assertIn('&lt;script&gt;', text)
        self.assertEqual(text, module.generate(self.repo)[0])

    def test_untagged_and_tag_at_head(self):
        self.commit('Initial commit')
        self.assertIn('Initial commit', module.generate(self.repo)[0])
        self.git('tag', 'v1')
        self.assertIn('No changes', module.generate(self.repo)[0])

    def test_unrelated_tag_is_not_used(self):
        self.commit('initial')
        branch = self.git('branch', '--show-current')
        self.git('checkout', '-qb', 'other')
        self.commit('unrelated')
        self.git('tag', 'v99')
        self.git('checkout', '-q', branch)
        self.commit('fix: actual branch')
        text, base, _ = module.generate(self.repo)
        self.assertIsNone(base)
        self.assertIn('actual branch', text)
        self.assertNotIn('unrelated', text)

    def test_existing_output_survives(self):
        self.commit('feat: one')
        output = self.repo / 'CHANGELOG.md'
        output.write_text('Keep this history', encoding='utf-8')
        import sys
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.repo), '--output', str(output)], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(), 'Keep this history')

    def test_empty_repository_fails(self):
        with self.assertRaises(ValueError):
            module.generate(self.repo)

if __name__ == '__main__':
    unittest.main()
