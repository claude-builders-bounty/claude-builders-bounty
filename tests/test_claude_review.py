#!/usr/bin/env python3
import unittest
import sys
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.claude_review import (
    PullRequestData,
    PullRequestRef,
    build_claude_review,
    build_review,
    changed_paths,
    parse_pr_url,
)


SAMPLE_DIFF = """diff --git a/app/auth/session.ts b/app/auth/session.ts
index 1111111..2222222 100644
--- a/app/auth/session.ts
+++ b/app/auth/session.ts
@@ -1,2 +1,3 @@
+export function requireSession() { return true; }
diff --git a/tests/session.test.ts b/tests/session.test.ts
index 3333333..4444444 100644
--- a/tests/session.test.ts
+++ b/tests/session.test.ts
@@ -1,2 +1,3 @@
+expect(requireSession()).toBe(true);
"""


class ClaudeReviewTests(unittest.TestCase):
    def test_parse_pr_url(self):
        ref = parse_pr_url("https://github.com/example/project/pull/42")
        self.assertEqual(ref.owner, "example")
        self.assertEqual(ref.repo, "project")
        self.assertEqual(ref.number, 42)

    def test_changed_paths(self):
        self.assertEqual(changed_paths(SAMPLE_DIFF), ["app/auth/session.ts", "tests/session.test.ts"])

    def test_review_has_required_sections(self):
        pr = PullRequestData(
            ref=PullRequestRef("example", "project", 42),
            title="Add session guard",
            author="reviewer",
            additions=2,
            deletions=0,
            changed_files=2,
            diff=SAMPLE_DIFF,
            url="https://github.com/example/project/pull/42",
        )
        review = build_review(pr)
        self.assertIn("### Summary of Changes", review)
        self.assertIn("### Identified Risks", review)
        self.assertIn("### Improvement Suggestions", review)
        self.assertIn("### Confidence Score: High", review)
        self.assertIn("Authentication or authorization surface", review)

    def test_claude_engine_returns_valid_markdown(self):
        pr = PullRequestData(
            ref=PullRequestRef("example", "project", 42),
            title="Add session guard",
            author="reviewer",
            additions=2,
            deletions=0,
            changed_files=2,
            diff=SAMPLE_DIFF,
            url="https://github.com/example/project/pull/42",
        )
        expected = "\n".join(
            [
                "## PR Review",
                "Source: https://github.com/example/project/pull/42",
                "Author: @reviewer",
                "",
                "### Summary of Changes",
                "This adds a session guard and a focused test.",
                "",
                "### Identified Risks",
                "- Authentication behavior changed and needs edge-case review.",
                "",
                "### Improvement Suggestions",
                "- Add a negative-path test.",
                "",
                "### Confidence Score: High",
                "The diff is small and includes a test.",
            ]
        )
        completed = CompletedProcess(["claude", "-p"], 0, stdout=expected, stderr="")

        with patch("scripts.claude_review.shutil.which", return_value="/usr/bin/claude"):
            with patch("scripts.claude_review.subprocess.run", return_value=completed):
                self.assertEqual(build_claude_review(pr), expected)

    def test_claude_engine_rejects_invalid_markdown(self):
        pr = PullRequestData(
            ref=PullRequestRef("example", "project", 42),
            title="Add session guard",
            author="reviewer",
            additions=2,
            deletions=0,
            changed_files=2,
            diff=SAMPLE_DIFF,
            url="https://github.com/example/project/pull/42",
        )
        completed = CompletedProcess(["claude", "-p"], 0, stdout="looks fine", stderr="")

        with patch("scripts.claude_review.shutil.which", return_value="/usr/bin/claude"):
            with patch("scripts.claude_review.subprocess.run", return_value=completed):
                self.assertIsNone(build_claude_review(pr))


if __name__ == "__main__":
    unittest.main()
