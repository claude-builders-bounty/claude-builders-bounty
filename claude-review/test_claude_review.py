import contextlib
import io
import json
import unittest
from unittest.mock import patch
import claude_review as reviewer

VALID = '## Summary\nThis change adds a guard. It validates inputs.\n\n## Identified Risks\n- None identified\n\n## Improvement Suggestions\n- Add an integration test.\n\n## Confidence Score\nMedium - Reviewed only the supplied diff.'
URL = 'https://github.com/owner/repo/pull/123'

class ReviewTests(unittest.TestCase):
    def test_exact_urls_only(self):
        self.assertEqual(reviewer.parse_pr_url(URL), ('owner','repo','123'))
        for bad in [URL+'invalid', URL+'?extra=yes', URL+'#x', URL.replace('https:', 'http:'), 'https://github.com/owner/../pull/1']:
            with self.assertRaises(ValueError): reviewer.parse_pr_url(bad)

    def test_format_validation(self):
        self.assertEqual(reviewer.validate_review(VALID), VALID)
        for bad in ['', 'Sorry, unavailable.', VALID.replace('## Summary', '## Overview'), VALID.replace('Medium -', 'Certain -'), VALID.replace('- Add an integration test.', ''), VALID.replace('This change adds a guard. It validates inputs.', 'One sentence.')]:
            with self.assertRaises(ValueError): reviewer.validate_review(bad)

    def test_diff_is_stdin_data_and_tools_disabled(self):
        with patch.object(reviewer, 'run', return_value=VALID) as run:
            reviewer.generate_review(URL, 'title', '+ untrusted `text`', 'model-name')
        args, kwargs = run.call_args
        self.assertNotIn('+ untrusted `text`', args[0])
        self.assertEqual(json.loads(kwargs['input_text'])['diff'], '+ untrusted `text`')
        self.assertIn('--restricted', args[0])
        self.assertEqual(args[0][args[0].index('--tools')+1], '')
        self.assertIn('mcp__*', args[0])

    def test_large_diff_fails_before_model(self):
        with patch.object(reviewer, 'run') as run:
            with self.assertRaises(ValueError): reviewer.generate_review(URL, 'title', 'x'*200001)
            run.assert_not_called()

    def run_cli(self, model_reply, heads=None, post=False):
        calls = []
        heads = iter(heads or ['a'*40]*3)
        def fake(cmd, input_text=None):
            calls.append((cmd, input_text))
            if cmd[:2] == ['gh','api']: return json.dumps({'title':'title','head':{'sha':next(heads)}})
            if cmd[:3] == ['gh','pr','diff']: return '+ some change'
            if cmd[0] == 'claude': return model_reply
            return 'comment URL'
        with patch.object(reviewer.shutil, 'which', return_value='/installed'), patch.object(reviewer, 'run', side_effect=fake), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            reviewer.main(['--pr', URL] + (['--post'] if post else []))
        return calls

    def test_default_never_posts(self):
        calls = self.run_cli(VALID)
        self.assertFalse(any(cmd[:3] == ['gh','pr','comment'] for cmd, _ in calls))

    def test_post_uses_stdin_only_after_validation(self):
        calls = self.run_cli(VALID, post=True)
        posts = [(cmd, body) for cmd, body in calls if cmd[:3] == ['gh','pr','comment']]
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][0][-2:], ['--body-file','-'])
        self.assertEqual(posts[0][1], VALID+'\n')

    def test_invalid_review_never_posts(self):
        with patch.object(reviewer, 'post_comment') as post:
            with self.assertRaises(ValueError): self.run_cli('Sorry, unavailable.', post=True)
            post.assert_not_called()

    def test_changed_head_never_posts(self):
        with patch.object(reviewer, 'post_comment') as post:
            with self.assertRaisesRegex(RuntimeError, 'stale'):
                self.run_cli(VALID, ['a'*40, 'a'*40, 'b'*40], post=True)
            post.assert_not_called()

    def test_post_function_also_validates(self):
        with patch.object(reviewer, 'run') as run:
            with self.assertRaises(ValueError): reviewer.post_comment(URL, 'error')
            run.assert_not_called()

if __name__ == '__main__': unittest.main()
