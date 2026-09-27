import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    'review', Path(__file__).resolve().parents[1] / 'claude_review.py'
)
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)


class ReviewTests(unittest.TestCase):
    def test_markdown_shape_and_two_sentence_summary(self):
        out = review.analyze('diff --git a/app/api/x b/app/api/x')
        for section in [
            '### Summary',
            '### Identified risks',
            '### Improvement suggestions',
            '### Confidence:',
        ]:
            self.assertIn(section, out)
        summary = out.split('### Summary\n', 1)[1].split('\n\n', 1)[0]
        self.assertGreaterEqual(summary.count('.'), 2)

    def test_changed_file_parser_uses_destination_path(self):
        diff = '\n'.join([
            'diff --git a/app/api/x.py b/app/api/x.py',
            'diff --git a/package-lock.json b/package-lock.json',
        ])
        self.assertEqual(review.changed_files(diff), ['app/api/x.py', 'package-lock.json'])

    def test_api_and_dependency_risks(self):
        diff = '\n'.join([
            'diff --git a/app/api/x.py b/app/api/x.py',
            'diff --git a/package-lock.json b/package-lock.json',
        ])
        out = review.analyze(diff)
        self.assertIn('Server/API code changed', out)
        self.assertIn('Dependency lockfile changed', out)

    def test_confidence_tiers(self):
        small = 'diff --git a/a b/a\n' + 'x' * 100
        medium = 'diff --git a/a b/a\n' + 'x' * 3000
        large = 'diff --git a/a b/a\n' + 'x' * 11000
        self.assertIn('### Confidence: Low', review.analyze(small))
        self.assertIn('### Confidence: Medium', review.analyze(medium))
        self.assertIn('### Confidence: High', review.analyze(large))


if __name__ == '__main__':
    unittest.main()
