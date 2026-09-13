import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'changelog.sh'


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        self.git('init', '-q')
        self.git('config', 'user.name', 'Test Author')
        self.git('config', 'user.email', 'test@example.invalid')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args],
                              check=True, capture_output=True, text=True)

    def commit(self, message):
        self.git('commit', '--allow-empty', '-qm', message)

    def run_script(self, *args):
        return subprocess.run(['bash', str(SCRIPT), '--repo', str(self.repo), *args],
                              cwd=self.repo, capture_output=True, text=True)

    def output(self):
        result = self.run_script('-o', '-')
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_no_tags_all_categories(self):
        for message in ('feat(ui): add café', 'fix: repair parser', 'refactor: simplify', 'chore: remove deprecated flag'):
            self.commit(message)
        result = self.output()
        for category in ('Added', 'Fixed', 'Changed', 'Removed'):
            self.assertIn('### ' + category, result)
        self.assertIn('café', result)
        self.assertEqual(result, self.output())

    def test_lightweight_tag_excludes_old_commits(self):
        self.commit('feat: old feature')
        self.git('tag', 'v1')
        self.commit('fix: new fix')
        result = self.output()
        self.assertNotIn('old feature', result)
        self.assertIn('new fix', result)

    def test_annotated_tag_at_head(self):
        self.commit('feat: original')
        self.git('tag', '-a', 'v1', '-m', 'release')
        self.assertIn('No changes', self.output())

    def test_empty_repository(self):
        self.assertIn('No changes', self.output())

    def test_breaking_markers_and_escaping(self):
        self.commit('feat!: incompatible [link](url) <script>')
        self.commit('fix: parser change\n\nBREAKING CHANGE: input format')
        result = self.output()
        self.assertEqual(result.count('BREAKING:'), 2)
        self.assertIn(r'\[link\]', result)
        self.assertIn('&lt;script&gt;', result)

    def test_existing_file_preserved_and_force(self):
        target = self.repo / 'CHANGELOG.md'
        target.write_text('historical release notes')
        self.assertNotEqual(self.run_script().returncode, 0)
        self.assertEqual(target.read_text(), 'historical release notes')
        self.assertEqual(self.run_script('--force').returncode, 0)
        self.assertTrue(target.read_text().startswith('# Changelog'))

    def test_symlink_refused_even_with_force(self):
        original = self.repo / 'original.txt'
        original.write_text('keep')
        (self.repo / 'CHANGELOG.md').symlink_to(original)
        self.assertNotEqual(self.run_script('--force').returncode, 0)
        self.assertEqual(original.read_text(), 'keep')

    def test_non_repo_fails_without_output(self):
        with tempfile.TemporaryDirectory() as other:
            result = self.run_script('--repo', other)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / 'CHANGELOG.md').exists())


if __name__ == '__main__':
    unittest.main()
