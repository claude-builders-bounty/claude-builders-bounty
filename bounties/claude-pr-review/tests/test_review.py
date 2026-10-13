import pathlib
import subprocess
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import claude_review as mod

VALID = '''## Summary
This change validates user inputs before processing them. It also adds a regression test.

## Risks
- `src/input.py`: Error messages may expose private data.

## Suggestions
- Add a test for input with unusual Unicode.

## Confidence
Confidence: Medium
'''

class UrlTests(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(mod.validate_pr_url('https://github.com/org/repo/pull/123'), 'https://github.com/org/repo/pull/123')
    def test_reject_non_github(self):
        for url in ('https://github.com.evil.example/o/r/pull/1', 'http://github.com/a/b/pull/1',
                    'https://github.com/a/b/pull/1?x=1', 'https://github.com/a/b/issues/1',
                    'https://a@github.com/a/b/pull/1', 'https://github.com/a/b/pull/0'):
            with self.subTest(url=url), self.assertRaises(mod.ReviewError):
                mod.validate_pr_url(url)

class ReviewValidationTests(unittest.TestCase):
    def test_valid(self):
        mod.validate_review(VALID)
    def test_bad_confidence(self):
        with self.assertRaises(mod.ReviewError):
            mod.validate_review(VALID.replace('Medium','99%'))
    def test_missing_section(self):
        with self.assertRaises(mod.ReviewError):
            mod.validate_review(VALID.replace('## Suggestions','### Not Suggestions'))
    def test_empty_list(self):
        with self.assertRaises(mod.ReviewError):
            mod.validate_review(VALID.replace('- Add a test for input with unusual Unicode.', ''))
    def test_duplicate_section(self):
        with self.assertRaises(mod.ReviewError):
            mod.validate_review(VALID + '\n## Summary\nExtra')

class SubprocessTests(unittest.TestCase):
    @patch('claude_review.subprocess.run')
    def test_diff_fetch_is_no_shell(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, 'diff --git a/x b/x\n', '')
        url = 'https://github.com/a/b/pull/9'
        self.assertTrue(mod.get_pr_diff(url).startswith('diff --git'))
        args, kwargs = run.call_args
        self.assertEqual(args[0], ['gh','pr','diff','--color=never',url])
        self.assertNotIn('shell', kwargs)
    @patch('claude_review.subprocess.run')
    def test_review_uses_subagent_and_disables_tools(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, VALID, '')
        result = mod.run_review('https://github.com/a/b/pull/9', 'diff --git a/a b/a\n')
        self.assertEqual(result, VALID)
        args, kwargs = run.call_args
        self.assertIn('pr-reviewer', args[0]); self.assertIn('--tools', args[0])
        self.assertIn('--disallowedTools', args[0])
        self.assertIn('UNTRUSTED', kwargs['input'])
    @patch('claude_review.subprocess.run')
    def test_failed_executable(self, run):
        run.side_effect = FileNotFoundError
        with self.assertRaises(mod.ReviewError):
            mod.get_pr_diff('https://github.com/a/b/pull/1')
    @patch('claude_review.subprocess.run')
    def test_nonzero(self, run):
        run.return_value = subprocess.CompletedProcess([], 1, '', 'not authenticated')
        with self.assertRaisesRegex(mod.ReviewError, 'not authenticated'):
            mod.get_pr_diff('https://github.com/a/b/pull/1')
    def test_limit(self):
        with self.assertRaises(mod.ReviewError):
            mod.run_review('https://github.com/a/b/pull/1', 'a' * (mod.MAX_DIFF_BYTES + 1))

if __name__ == '__main__':
    unittest.main()
