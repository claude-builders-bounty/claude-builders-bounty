import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('generator', ROOT / 'generate_changelog.py')
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='changelog-test-')
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / 'repo with spaces'
        self.repo.mkdir()
        self.env = {**os.environ, 'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 'Fixture', 'GIT_AUTHOR_EMAIL': 'fixture@example.invalid',
                    'GIT_COMMITTER_NAME': 'Fixture', 'GIT_COMMITTER_EMAIL': 'fixture@example.invalid'}
        for key in list(self.env):
            if key.startswith(('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_CONFIG_COUNT')):
                self.env.pop(key)
        self.git('init', '-q', '--initial-branch=main', '--template=')
        self.git('config', 'core.hooksPath', os.devnull)
        self.git('config', 'commit.gpgsign', 'false')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], env=self.env, stderr=subprocess.DEVNULL).decode().strip()

    def commit(self, message):
        self.git('commit', '-q', '--allow-empty', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / 'generate_changelog.py'), '--repo', str(self.repo), *args], env=self.env, capture_output=True, text=True)

    def test_all_four_categories_and_subject_framing(self):
        subjects = ['feat(api): add endpoint', 'fix: null response', 'perf: faster', 'remove!: obsolete API', 'fix: pipe | tab\t <script> [link](https://example.invalid)']
        shas = [self.commit(s) for s in subjects]
        result = self.run_cli('--stdout')
        self.assertEqual(result.returncode, 0, result.stderr)
        for section in generator.CATEGORIES:
            self.assertIn('### ' + section, result.stdout)
        for sha in shas:
            self.assertEqual(result.stdout.count('(`' + sha + '`)'), 1)
        self.assertIn('&lt;script&gt;', result.stdout)
        self.assertIn('\\[link\\]\\(', result.stdout)

    def test_lightweight_and_annotated_tag_boundaries(self):
        for annotated in (False, True):
            with self.subTest(annotated=annotated):
                old = self.commit('old release')
                tag = 'v' + str(annotated)
                self.git('tag', *(['-a', tag, '-m', 'release'] if annotated else [tag]))
                new = self.commit('fix: after release')
                result = self.run_cli('--stdout')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn('(`' + old + '`) ', result.stdout)
                self.assertNotIn('- old release', result.stdout)
                self.assertIn('(`' + new + '`)', result.stdout)

    def test_side_branch_tag_does_not_hide_mainline_commits(self):
        self.commit('base')
        self.git('tag', 'v1')
        self.git('checkout', '-q', '-b', 'topic')
        topic = self.commit('feat: topic')
        self.git('tag', 'topic-release')
        self.git('checkout', '-q', 'main')
        main = self.commit('fix: mainline')
        self.git('merge', '-q', '--no-ff', 'topic', '-m', 'merge topic')
        merge = self.git('rev-parse', 'HEAD')
        result = self.run_cli('--stdout')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Since tag v1 ', result.stdout)
        for sha in (topic, main, merge):
            self.assertEqual(result.stdout.count('(`' + sha + '`)'), 1)

    def test_tagged_head_produces_empty_sections(self):
        self.commit('init')
        self.git('tag', 'v1')
        result = self.run_cli('--stdout')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count('- None.'), 4)

    def test_no_tag_and_empty_repository(self):
        self.assertNotEqual(self.run_cli('--stdout').returncode, 0)
        self.commit('Add initial implementation')
        result = self.run_cli('--stdout')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('No first-parent release tag', result.stdout)
        self.assertIn('### Added\n\n- Add initial', result.stdout)

    def test_existing_handwritten_file_is_not_overwritten(self):
        self.commit('init')
        output = Path(self.temp.name) / 'CHANGELOG.md'
        output.write_text('Handwritten release notes\n')
        self.assertNotEqual(self.run_cli('--output', str(output)).returncode, 0)
        self.assertEqual(output.read_text(), 'Handwritten release notes\n')

    def test_repeatability_and_preservation_of_manual_sections(self):
        self.commit('feat: first')
        output = Path(self.temp.name) / 'CHANGELOG.md'
        self.assertEqual(self.run_cli('--output', str(output)).returncode, 0)
        output.write_text(output.read_text() + '\n## [v0]\n\nManual history.\n')
        before = output.read_bytes()
        self.assertEqual(self.run_cli('--output', str(output)).returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        self.commit('fix: second')
        self.assertEqual(self.run_cli('--output', str(output)).returncode, 0)
        self.assertTrue(output.read_text().endswith('\n## [v0]\n\nManual history.\n'))
        self.assertIn('- fix: second', output.read_text())

    def test_ambiguous_markers_and_symlink_are_rejected(self):
        self.commit('init')
        output = Path(self.temp.name) / 'CHANGELOG.md'
        output.write_text(generator.START * 2 + generator.END)
        before = output.read_bytes()
        self.assertNotEqual(self.run_cli('--output', str(output)).returncode, 0)
        self.assertEqual(output.read_bytes(), before)
        link = Path(self.temp.name) / 'link.md'
        try:
            link.symlink_to(output)
        except OSError:
            self.skipTest('Symlinks not permitted on this platform')
        self.assertNotEqual(self.run_cli('--output', str(link)).returncode, 0)
        self.assertEqual(output.read_bytes(), before)

    def test_shallow_history_is_rejected(self):
        self.commit('release')
        self.git('tag', 'v1')
        self.commit('feat: after release')
        shallow = Path(self.temp.name) / 'shallow'
        subprocess.check_call(['git', 'clone', '-q', '--depth=1', '--template=', self.repo.as_uri(), str(shallow)], env=self.env)
        self.repo = shallow
        result = self.run_cli('--stdout')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Shallow history', result.stderr)

    def test_nonconventional_subject_mapping(self):
        for subject, expected in [('Added tests', 'Added'), ('Fixed bug', 'Fixed'), ('Remove old API', 'Removed'), ('docs: remove ambiguity', 'Changed'), ('Revert previous feature', 'Changed')]:
            self.assertEqual(generator.category(subject), expected)


if __name__ == '__main__':
    unittest.main()
