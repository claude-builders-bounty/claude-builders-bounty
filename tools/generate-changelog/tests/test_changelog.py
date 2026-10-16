"""Offline integration tests for changelog.sh. Requires git and bash."""
import pathlib
import subprocess
import tempfile
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'changelog.sh'

def run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=check)

class ChangelogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='bounty1-')
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        run('git', 'init', '-q', str(self.repo))
        run('git', 'config', 'user.name', 'Offline Test', cwd=self.repo)
        run('git', 'config', 'user.email', 'offline@example.invalid', cwd=self.repo)
        self.commit('init: starting repo')

    def commit(self, subject):
        dummy = self.repo / 'data.txt'
        with dummy.open('a', encoding='utf-8') as f:
            f.write('data\n')
        run('git', 'add', 'data.txt', cwd=self.repo)
        run('git', 'commit', '-qm', subject, cwd=self.repo)

    def invoke(self, *args, check=True):
        return run('bash', str(SCRIPT), '--repo', str(self.repo), *args, check=check)

    def test_sections_and_categories_since_tag(self):
        run('git', 'tag', 'v1.0', cwd=self.repo)
        messages = ['feat(api): add endpoint', 'fix: close bug', 'docs: revise usage',
                    'remove: deprecated command', 'miscellaneous improvement']
        for subject in messages:
            self.commit(subject)
        self.invoke()
        data = (self.repo / 'CHANGELOG.md').read_text()
        for group in ('Added', 'Fixed', 'Changed', 'Removed'):
            self.assertIn('### ' + group, data)
        self.assertIn('tag `v1.0`', data)
        self.assertNotIn('init: starting repo', data)
        for subject in messages:
            self.assertEqual(data.count(subject), 1)
        self.assertTrue(data.index('### Added') < data.index('### Fixed') < data.index('### Changed') < data.index('### Removed'))

    def test_reachable_tag_not_latest_timestamp(self):
        run('git', 'tag', 'v1.0', cwd=self.repo)
        self.commit('feat: one')
        run('git', 'tag', 'v1.1', cwd=self.repo)
        self.commit('fix: two')
        self.invoke()
        data = (self.repo / 'CHANGELOG.md').read_text()
        self.assertIn('tag `v1.1`', data)
        self.assertIn('fix: two', data)
        self.assertNotIn('feat: one', data)

    def test_no_tags_includes_history(self):
        self.invoke()
        self.assertIn('init: starting repo', (self.repo/'CHANGELOG.md').read_text())

    def test_tag_at_head_no_changes(self):
        run('git', 'tag', 'v1', cwd=self.repo)
        self.invoke()
        data = (self.repo/'CHANGELOG.md').read_text()
        self.assertIn('tag `v1`', data)
        self.assertEqual(data.count('_None._'), 4)

    def test_excludes_merge_commits(self):
        run('git', 'tag', 'v1', cwd=self.repo)
        base = run('git', 'branch', '--show-current', cwd=self.repo).stdout.strip()
        run('git', 'checkout', '-qb', 'feature', cwd=self.repo)
        self.commit('feat: branch')
        run('git', 'checkout', '-q', base, cwd=self.repo)
        self.commit('fix: main')
        run('git', 'merge', '--no-ff', '-m', 'Merge feature PR', 'feature', cwd=self.repo)
        self.invoke()
        data = (self.repo/'CHANGELOG.md').read_text()
        self.assertNotIn('Merge feature PR', data)
        self.assertIn('feat: branch', data)
        self.assertIn('fix: main', data)

    def test_no_overwrite_by_default(self):
        path = self.repo/'CHANGELOG.md'
        path.write_text('OWNER FILE\n')
        result = self.invoke(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(path.read_text(), 'OWNER FILE\n')
        self.invoke('--force')
        self.assertIn('Changelog', path.read_text())

    def test_custom_output_path(self):
        self.invoke('--output', 'sample.md')
        self.assertTrue((self.repo/'sample.md').exists())
        self.assertFalse((self.repo/'CHANGELOG.md').exists())

    def test_fails_outside_repo(self):
        result = run('bash', str(SCRIPT), '--repo', self.tmp.name, check=False)
        self.assertNotEqual(result.returncode, 0)

    def test_shell_injection_is_inert(self):
        run('git', 'tag', 'v1', cwd=self.repo)
        victim = self.repo/'SHOULD_NOT_EXIST'
        self.commit('fix: $(touch SHOULD_NOT_EXIST)')
        self.invoke()
        self.assertFalse(victim.exists())
        self.assertIn('$(touch SHOULD_NOT_EXIST)', (self.repo/'CHANGELOG.md').read_text())

    def test_symlink_not_overwritten(self):
        target = self.repo/'target.md'
        target.write_text('SAFE\n')
        try:
            (self.repo/'CHANGELOG.md').symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable on this machine')
        result = self.invoke('--force', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(target.read_text(), 'SAFE\n')

    def test_argument_errors(self):
        for args in (('--output',), ('--repo',), ('--unknown',)):
            with self.subTest(args=args):
                self.assertNotEqual(self.invoke(*args, check=False).returncode, 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
