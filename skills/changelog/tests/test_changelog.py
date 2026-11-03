"""Black-box tests using synthetic local git histories, not model-generated evidence."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ChangelogTests(unittest.TestCase):
    def setUp(self):
        parent = os.environ.get('CHANGELOG_TEST_TMPDIR', os.environ.get('TMPDIR'))
        self.tmp = tempfile.TemporaryDirectory(dir=parent)
        self.repo = Path(self.tmp.name) / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Synthetic Test Author')
        self.git('config', 'user.email', 'test@example.invalid')
        self.commit('chore: initial baseline')

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args],
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit(self, message):
        self.git('-c', 'core.hooksPath=/dev/null', 'commit', '-q', '--allow-empty', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def run_cli(self, *args):
        return subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(self.repo), *args],
                              capture_output=True, text=True)

    def output(self):
        return (self.repo / 'CHANGELOG.md').read_text()

    def test_01_categories_since_last_tag(self):
        self.commit('feat: obsolete feature')
        self.git('tag', 'v1.0.0')
        for msg in ['feat(cli): add export command', 'fix: handle empty input',
                    'perf: reduce memory use', 'remove: delete obsolete flag']:
            self.commit(msg)
        p = self.run_cli()
        self.assertEqual(p.returncode, 0, p.stderr)
        for heading in ['Added', 'Fixed', 'Changed', 'Removed']:
            self.assertIn('### ' + heading, self.output())
        self.assertNotIn('obsolete feature', self.output())

    def test_02_no_tags_uses_full_history(self):
        self.commit('feat: support Unicode 입력')
        p = self.run_cli()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('Unicode 입력', self.output())
        self.assertNotIn('initial baseline', self.output())

    def test_03_idempotent_rerun(self):
        self.commit('fix: avoid duplicate output')
        self.assertEqual(self.run_cli().returncode, 0)
        before = (self.repo / 'CHANGELOG.md').read_bytes()
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(before, (self.repo / 'CHANGELOG.md').read_bytes())

    def test_04_preserves_manual_and_historical_sections(self):
        history = '## [1.0.0] - 2025-01-01\n\n### Fixed\n- Historical entry.\n'
        p = self.repo / 'CHANGELOG.md'
        p.write_text('# Changelog\n\n## [Unreleased]\n\nManual note.\n\n' + history)
        self.commit('fix: new correction')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertIn('Manual note.', self.output())
        self.assertTrue(self.output().endswith(history))

    def test_05_dry_run_never_writes(self):
        self.commit('feat: preview command')
        p = self.run_cli('--dry-run')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('preview command', p.stdout)
        self.assertFalse((self.repo / 'CHANGELOG.md').exists())

    def test_06_invalid_option_like_ref_does_not_write(self):
        p = self.run_cli('--from=--all')
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.repo / 'CHANGELOG.md').exists())

    def test_07_nonancestor_range_rejected(self):
        old = self.git('rev-parse', 'HEAD')
        newer = self.commit('fix: later commit')
        p = self.run_cli('--from', newer, '--to', old)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((self.repo / 'CHANGELOG.md').exists())

    def test_08_breaking_chore_not_dropped(self):
        self.commit('chore!: remove old build support\n\nBREAKING CHANGE: requires a newer runtime')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertIn('**BREAKING**', self.output())
        self.assertIn('remove old build support', self.output())

    def test_09_hostile_markdown_is_escaped_not_executed(self):
        marker = self.repo / 'SHOULD_NOT_EXIST'
        self.commit('fix: <script>alert(1)</script> [link](https://example.invalid) $(touch SHOULD_NOT_EXIST)')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertFalse(marker.exists())
        self.assertNotIn('<script>', self.output())
        self.assertIn('\\[link\\]', self.output())

    def test_10_control_delimiter_in_commit_body(self):
        self.commit('fix: keep complete record\n\nBody has ---END--- and \x1e and pipes | here.')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(self.output().count('keep complete record'), 1)

    def test_11_crlf_history_preserved_byte_for_byte(self):
        history = b'## [0.9] - 2025-01-01\r\n\r\nOld history.\r\n'
        p = self.repo / 'CHANGELOG.md'
        p.write_bytes(b'# Changelog\r\n\r\n## [Unreleased]\r\n\r\n' + history)
        self.commit('fix: retain historical bytes')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertTrue(p.read_bytes().endswith(history))

    def test_12_symlink_output_refused(self):
        target = Path(self.tmp.name) / 'unrelated.txt'
        target.write_text('DO NOT TOUCH')
        (self.repo / 'CHANGELOG.md').symlink_to(target)
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertEqual(target.read_text(), 'DO NOT TOUCH')

    def test_13_git_metadata_output_refused(self):
        p = self.repo / '.git' / 'config'
        before = p.read_bytes()
        self.assertNotEqual(self.run_cli('--output', str(p)).returncode, 0)
        self.assertEqual(before, p.read_bytes())

    def test_14_no_repo_mutation_except_changelog(self):
        self.commit('feat: report safe changes')
        head = self.git('rev-parse', 'HEAD')
        refs = self.git('show-ref', '--head')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertEqual(head, self.git('rev-parse', 'HEAD'))
        self.assertEqual(refs, self.git('show-ref', '--head'))
        self.assertEqual(self.git('status', '--porcelain'), '?? CHANGELOG.md')

    def test_15_reject_broken_managed_marker_without_writing(self):
        p = self.repo / 'CHANGELOG.md'
        before = '# Changelog\n\n## [Unreleased]\n<!-- generated-changelog:start -->\nmanual text\n'
        p.write_text(before)
        self.assertNotEqual(self.run_cli().returncode, 0)
        self.assertEqual(p.read_text(), before)

    def test_16_empty_range_valid(self):
        self.git('tag', 'v1.0.0')
        self.assertEqual(self.run_cli().returncode, 0)
        self.assertIn('No user-facing changes', self.output())

    def test_17_shallow_history_without_tag_refused(self):
        self.commit('feat: recent change')
        shallow = Path(self.tmp.name) / 'shallow.git'
        subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'clone', '--bare', '--depth=1',
                        self.repo.as_uri(), str(shallow)], check=True, capture_output=True)
        output = Path(self.tmp.name) / 'incomplete.md'
        p = subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(shallow),
                            '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse(output.exists())

    def test_18_linked_worktree_common_metadata_refused(self):
        linked = Path(self.tmp.name) / 'linked'
        self.git('-c', 'core.hooksPath=/dev/null', 'worktree', 'add', '-q', '--detach', str(linked), 'HEAD')
        target = self.repo / '.git' / 'config'
        before = target.read_bytes()
        p = subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(linked),
                            '--output', str(target)], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(target.read_bytes(), before)

    def test_19_linked_worktree_git_pointer_refused(self):
        linked = Path(self.tmp.name) / 'linked'
        self.git('-c', 'core.hooksPath=/dev/null', 'worktree', 'add', '-q', '--detach', str(linked), 'HEAD')
        target = linked / '.git'
        before = target.read_bytes()
        p = subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(linked),
                            '--output', str(target)], capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertEqual(target.read_bytes(), before)

    def test_20_nonrepository_refused(self):
        empty = Path(self.tmp.name) / 'not-a-repo'
        empty.mkdir()
        p = subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(empty)],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((empty / 'CHANGELOG.md').exists())

    def test_21_repository_without_commits_refused(self):
        empty = Path(self.tmp.name) / 'empty-git'
        empty.mkdir()
        subprocess.run(['git', '-C', str(empty), 'init', '-q'], check=True, capture_output=True)
        p = subprocess.run(['bash', str(ROOT / 'changelog.sh'), '--repo', str(empty)],
                           capture_output=True, text=True)
        self.assertNotEqual(p.returncode, 0)
        self.assertFalse((empty / 'CHANGELOG.md').exists())

    def test_22_explicit_commit_bounds(self):
        old = self.commit('feat: excluded old entry')
        chosen = self.commit('fix: explicitly selected change')
        self.commit('feat: excluded future entry')
        p = self.run_cli('--from', old, '--to', chosen)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('explicitly selected change', self.output())
        self.assertNotIn('excluded old entry', self.output())
        self.assertNotIn('excluded future entry', self.output())


if __name__ == '__main__':
    unittest.main(verbosity=2)
