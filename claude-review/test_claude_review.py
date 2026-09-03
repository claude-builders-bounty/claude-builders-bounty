#!/usr/bin/env python3
import unittest

from claude_review import review


class ReviewTests(unittest.TestCase):
    def test_required_sections_and_confidence(self):
        meta = {"title": "Small change", "files": [{"path": "app.py"}], "additions": 10, "deletions": 2}
        output = review(meta, "+print('hello')\n")
        self.assertIn("## Summary", output)
        self.assertIn("## Identified risks", output)
        self.assertIn("## Improvement suggestions", output)
        self.assertIn("## Confidence", output)
        self.assertIn("Medium", output)

    def test_credential_signal_is_reported(self):
        meta = {"title": "Config update", "files": [{"path": "config.py"}], "additions": 5, "deletions": 0}
        output = review(meta, "+API_KEY = 'placeholder'\n")
        self.assertIn("Potential credential-sensitive change", output)

    def test_execution_surface_signal_is_reported(self):
        meta = {"title": "Runner update", "files": [{"path": "runner.py"}], "additions": 5, "deletions": 0}
        output = review(meta, "+subprocess.run(['echo', 'ok'])\n")
        self.assertIn("Execution surface changed", output)

    def test_large_diff_signal_is_reported(self):
        meta = {"title": "Large refactor", "files": [{"path": "core.py"}], "additions": 801, "deletions": 1}
        output = review(meta, "+def changed():\n+    pass\n")
        self.assertIn("Large diff increases review risk", output)


if __name__ == "__main__":
    unittest.main()
