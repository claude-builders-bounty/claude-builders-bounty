import contextlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from reviewer.github import parse_pr_url, fetch_pr
from reviewer.engine import HeuristicEngine
from reviewer.__main__ import main

ROOT = Path(__file__).resolve().parent


def snapshot(patch_text='@@ -1 +1 @@\n-old\n+new', filename='src/app.py'):
    return {'pr_url': 'https://github.com/example/repo/pull/1', 'files': [{'filename': filename, 'patch': patch_text}]}


class ReviewTests(unittest.TestCase):
    def test_url(self):
        self.assertEqual(parse_pr_url('https://github.com/psf/requests/pull/7128/'), ('psf', 'requests', 7128))
        for url in ['http://github.com/a/b/pull/1', 'https://github.com.evil/a/b/pull/1', 'https://github.com/a/b/pull/0', 'https://github.com/a/b/pull/1?x=y', 'https://github.com/a/b/pull/1#x', 'https://github.com/a/../pull/1', 'https://user@github.com/a/b/pull/1']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                parse_pr_url(url)

    def test_structure(self):
        result = HeuristicEngine().review(snapshot())
        for heading in ('Summary of changes', 'Identified risks', 'Improvement suggestions', 'Confidence'):
            self.assertIn('## '+heading, result)
        self.assertIn('1 additions and 1 deletions', result)
        self.assertIn('**Med**', result)

    def test_empty(self):
        self.assertIn('**Low**', HeuristicEngine().review(snapshot('')))
        self.assertIn('No textual changed lines', HeuristicEngine().review(snapshot('')))
        self.assertIn('**Low**', HeuristicEngine().review({'pr_url': snapshot()['pr_url'], 'files': []}))

    def test_large(self):
        result = HeuristicEngine().review(snapshot('@@ -0,0 +1,100000 @@\n' + '+line\n'*100000))
        self.assertIn('Large diff', result)
        self.assertIn('**Low**', result)
        self.assertLess(len(result), 4000)

    def test_confidence_and_redaction(self):
        secret = 'AKIA'+'A'*16
        result = HeuristicEngine().review(snapshot('@@ -0,0 +1 @@\n+'+secret))
        self.assertIn('**High**', result)
        self.assertNotIn(secret, result)
        self.assertIn('src/app.py:1', result)

    def test_added_header_like_line(self):
        result = HeuristicEngine().review(snapshot('@@ -0,0 +1 @@\n+++content'))
        self.assertIn('1 additions', result)

    def test_missing_and_mismatch(self):
        data = snapshot()
        data['changed_files'] = 2
        self.assertIn('**Low**', HeuristicEngine().review(data))
        data['changed_files'] = 1
        data['additions'] = 999
        self.assertIn('incomplete', HeuristicEngine().review(data))

    def test_test_detection_and_path_signals(self):
        data = snapshot(filename='migrations/001.sql')
        data['files'].append({'filename': 'tests/test_app.py', 'patch': '@@ -0,0 +1 @@\n+assert True'})
        result = HeuristicEngine().review(data)
        self.assertIn('Database/schema', result)
        self.assertIn('1 added test lines', result)
        self.assertNotIn('no added test lines', result)

    def test_untrusted_metadata(self):
        data = snapshot(filename='<script>evil</script>')
        data['title'] = '\n## forged'
        result = HeuristicEngine().review(data)
        self.assertNotIn('<script>', result)
        self.assertNotIn('\n## forged', result)

    @patch('reviewer.github.get_json')
    def test_pagination(self, get):
        meta = {'title': 'x', 'head': {'sha': 'h'}, 'base': {'sha': 'b'}, 'changed_files': 101, 'additions': 0, 'deletions': 0}
        get.side_effect = [meta, [{'filename': str(i)} for i in range(100)], [{'filename': 'last'}], meta]
        self.assertEqual(len(fetch_pr(snapshot()['pr_url'])['files']), 101)
        self.assertIn('page=2', get.call_args_list[2].args[0])

    @patch('reviewer.github.get_json')
    def test_changed_head(self, get):
        meta = {'head': {'sha': 'h'}, 'base': {'sha': 'b'}}
        get.side_effect = [meta, [], {'head': {'sha': 'other'}, 'base': {'sha': 'b'}}]
        with self.assertRaisesRegex(ValueError, 'changed'):
            fetch_pr(snapshot()['pr_url'])

    def test_real_pr_cli(self):
        for i in (1, 2):
            path = ROOT / f'sample-outputs/evidence/pr-{i}.json'
            data = json.loads(path.read_text())
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(main(['--pr', data['pr_url'], '--snapshot', str(path)]), 0)
            committed = (ROOT / f'sample-outputs/pr-{i}.md').read_text()
            self.assertTrue(committed.endswith(output.getvalue()))

    def test_cli_errors(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--pr', 'bad']), 1)
            self.assertEqual(main(['--pr', snapshot()['pr_url'], '--snapshot', str(ROOT / 'sample-outputs/evidence/pr-1.json')]), 1)


if __name__ == '__main__':
    unittest.main()
