import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'changelog.py'
spec = importlib.util.spec_from_file_location('changelog', SCRIPT)
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'user.email', 'test@example.invalid')
        self.commit('feat: before release')

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def commit(self, subject):
        self.git('commit', '--allow-empty', '-m', subject)

    def test_nearest_annotated_tag_and_all_four_categories(self):
        self.git('tag', '-a', 'v1.0', '-m', 'release')
        for text in ['feat(api): add export', 'fix: CSV quoting', 'perf: faster parser', 'refactor!: remove legacy endpoint']:
            self.commit(text)
        result = changelog.generate(self.repo)
        self.assertNotIn('before release', result)
        self.assertIn('Commits since v1.0.', result)
        for name, message in [('Added', 'feat(api): add export'), ('Fixed', 'fix: CSV quoting'),
                              ('Changed', 'perf: faster parser'), ('Removed', 'refactor!: remove legacy endpoint')]:
            self.assertIn(message, result.split('### ' + name + '\n')[1].split('### ')[0])
        self.assertEqual(result, changelog.generate(self.repo))

    def test_no_tags_and_nonconventional_subjects(self):
        self.commit('Fix broken links')
        self.commit('Remove unused helper')
        self.commit('Update docs [guide] <script>')
        result = changelog.generate(self.repo)
        self.assertIn('before release', result)
        self.assertIn('All reachable commits', result)
        self.assertIn(r'\[guide\] \<script\>', result)

    def test_tag_on_other_branch_does_not_hide_main_history(self):
        self.git('tag', 'v1')
        self.git('switch', '-c', 'other')
        self.commit('feat: unmerged')
        self.git('tag', 'v99')
        self.git('switch', 'main')
        self.commit('fix: main change')
        result = changelog.generate(self.repo)
        self.assertIn('Commits since v1.', result)
        self.assertIn('main change', result)
        self.assertNotIn('unmerged', result)
        with self.assertRaises(ValueError):
            changelog.generate(self.repo, 'v99')

    def test_tag_at_head_has_empty_sections(self):
        self.git('tag', 'v1')
        self.assertEqual(changelog.generate(self.repo).count('- No changes.'), 4)

    def test_shallow_clone_rejected(self):
        shallow = self.repo / 'shallow'
        subprocess.run(['git', 'clone', '--depth=1', self.repo.as_uri(), str(shallow)],
                       check=True, capture_output=True)
        with self.assertRaisesRegex(ValueError, 'Shallow'):
            changelog.generate(shallow)

    def test_cli_never_overwrites_existing_output_by_default(self):
        import sys
        output = self.repo / 'CHANGELOG.md'
        output.write_text('existing release history', encoding='utf-8')
        result = subprocess.run([sys.executable, str(SCRIPT), '--repo', str(self.repo)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(output.read_text(encoding='utf-8'), 'existing release history')


if __name__ == '__main__':
    unittest.main()
