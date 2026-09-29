import unittest
from changelog import read_commits, update_changelog, parse_commits, render

class ChangelogTests(unittest.TestCase):
    def test_tag_range_applies_to_actual_log(self):
        calls = []
        def run(repo, *args, **kwargs):
            calls.append(args)
            if args[0] == 'describe': return 'v1.0.0'
            if args == ('rev-parse', '--is-shallow-repository'): return 'false'
            if args[0] == 'log': return 'a' * 40 + '\tfix: new fix'
            return 'a' * 40
        tag, commits = read_commits('.', run)
        self.assertEqual(tag, 'v1.0.0')
        self.assertIn(('log', '--no-merges', '--format=%H%x09%s', 'v1.0.0..HEAD', '--'), calls)
        self.assertEqual(len(commits), 1)

    def test_real_repository_snapshot(self):
        # Verified against GitHub commits API at this immutable source revision.
        rows = '1aeae2adc82d33f971fd7731644348dcdd24b5a6\tfeat: initial README with bounty board\na80a580e34190a6bb8649a1b75a9fec8312bea5c\tInitial commit'
        out = render(parse_commits(rows))
        self.assertIn('### Added\n- feat: initial README with bounty board (1aeae2a)', out)
        self.assertIn('### Changed\n- Initial commit (a80a580)', out)

    def test_all_categories_and_released_sections(self):
        released = '## [1.0.0] - 2026-01-01\n\n### Added\n- Preserve me\n'
        old = '# Changelog\n\n## [Unreleased]\n\n- old\n\n' + released
        commits = [(str(i) * 40, s) for i, s in enumerate(['feat(api): new', 'fix: issue', 'docs: guide', 'feat: remove old API'])]
        out = update_changelog(old, commits)
        self.assertTrue(out.endswith(released))
        for name in ['Added', 'Fixed', 'Changed', 'Removed']: self.assertIn('### ' + name, out)
        self.assertEqual(update_changelog(out, commits), out)

    def test_empty_leaves_existing_untouched(self):
        self.assertEqual(update_changelog('manual notes\n', []), 'manual notes\n')

    def test_no_tags_uses_head(self):
        calls = []
        def run(repo, *args, **kwargs):
            calls.append(args)
            return None if args[0] == 'describe' else ('false' if args[-1] == '--is-shallow-repository' else '')
        read_commits('.', run)
        self.assertIn(('log', '--no-merges', '--format=%H%x09%s', 'HEAD', '--'), calls)

    def test_shallow_history_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Shallow'):
            read_commits('.', lambda repo, *args, **kwargs: 'true')

    def test_ambiguous_sections_rejected(self):
        with self.assertRaises(ValueError): update_changelog('## Unreleased\n## Unreleased\n', [('a'*40, 'fix: a')])

if __name__ == '__main__': unittest.main()
