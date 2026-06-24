"""
Tests for claude_review.py

Run:  python -m unittest tests.test_claude_review
"""

import json
import sys
import types
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── make sure the project root is importable ──────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))
import claude_review


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_METADATA = {
    "title": "Fix null pointer in user lookup",
    "number": 42,
    "author": {"login": "alice"},
    "baseRefName": "main",
    "headRefName": "fix/null-user",
    "additions": 15,
    "deletions": 3,
    "changedFiles": 2,
    "url": "https://github.com/example/repo/pull/42",
    "isDraft": False,
    "state": "OPEN",
    "body": "Fixes #37 — null pointer when user ID is missing.",
}

SAMPLE_DIFF = """\
diff --git a/src/user.py b/src/user.py
index abc..def 100644
--- a/src/user.py
+++ b/src/user.py
@@ -10,7 +10,9 @@ def get_user(user_id):
-    return db.query(User).filter_by(id=user_id).first()
+    if user_id is None:
+        raise ValueError("user_id must not be None")
+    return db.query(User).filter_by(id=user_id).first()
"""

SAMPLE_REVIEW = """\
## 🤖 Automated PR Review

> Reviewed by pr-reviewer · PR #42 · Fix null pointer in user lookup

---

### Summary

The PR adds a guard clause for a missing `user_id`, preventing a null-pointer
error at the database layer. The change is minimal and targeted.

**Verdict:** ✅ Approve

---

### Issues

No issues found — the changes look clean.

---

### Checklist

| | Item |
|---|---|
| ❌ | New code has corresponding tests |
| ✅ | Error cases are handled |
| ✅ | No secrets or credentials in code |
| ✅ | Changes are backward-compatible |
| ✅ | Commit messages are clear |

---

<details>
<summary>Stats</summary>

- Files changed: 2
- Additions: +15 / Deletions: -3
- Findings: 0 critical, 0 high, 0 medium, 0 low, 1 suggestion

</details>
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGitHubHelpers(unittest.TestCase):
    """Unit tests for the gh CLI wrapper functions."""

    @patch("claude_review.subprocess.run")
    def test_run_gh_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output\n", stderr="")
        result = claude_review.run_gh(["pr", "view", "1"])
        self.assertEqual(result, "output")

    @patch("claude_review.subprocess.run")
    def test_run_gh_failure(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="not found")
        with self.assertRaises(RuntimeError):
            claude_review.run_gh(["pr", "view", "999"])

    @patch("claude_review.run_gh")
    def test_get_pr_metadata_no_repo(self, mock_gh):
        mock_gh.return_value = json.dumps(SAMPLE_METADATA)
        result = claude_review.get_pr_metadata(42, None)
        self.assertEqual(result["title"], "Fix null pointer in user lookup")
        self.assertEqual(result["number"], 42)
        # Should NOT pass --repo flags
        call_args = mock_gh.call_args[0][0]
        self.assertNotIn("--repo", call_args)

    @patch("claude_review.run_gh")
    def test_get_pr_metadata_with_repo(self, mock_gh):
        mock_gh.return_value = json.dumps(SAMPLE_METADATA)
        claude_review.get_pr_metadata(42, "owner/repo")
        call_args = mock_gh.call_args[0][0]
        self.assertIn("--repo", call_args)
        self.assertIn("owner/repo", call_args)

    @patch("claude_review.run_gh")
    def test_get_pr_diff(self, mock_gh):
        mock_gh.return_value = SAMPLE_DIFF
        result = claude_review.get_pr_diff(42, None)
        self.assertIn("user_id", result)

    @patch("claude_review.run_gh")
    def test_get_existing_comments(self, mock_gh):
        mock_gh.return_value = "First comment\nSecond comment"
        comments = claude_review.get_existing_comments(42, None)
        self.assertEqual(len(comments), 2)
        self.assertIn("First comment", comments)

    @patch("claude_review.run_gh")
    def test_post_comment(self, mock_gh):
        mock_gh.return_value = ""
        claude_review.post_comment(42, "review body", None)
        call_args = mock_gh.call_args[0][0]
        self.assertIn("pr", call_args)
        self.assertIn("comment", call_args)
        self.assertIn("42", call_args)
        self.assertIn("review body", call_args)


class TestReviewGeneration(unittest.TestCase):
    """Tests for the Claude API integration."""

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("claude_review.anthropic.Anthropic")
    def test_generate_review_returns_text(self, mock_anthropic):
        # Mock the Anthropic client chain
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_REVIEW)]
        mock_client.messages.create.return_value = mock_response

        result = claude_review.generate_review(SAMPLE_METADATA, SAMPLE_DIFF, [])
        self.assertIn("🤖 Automated PR Review", result)
        self.assertIn("Verdict", result)

    @patch.dict("os.environ", {}, clear=True)
    def test_generate_review_missing_api_key(self):
        # ANTHROPIC_API_KEY not set → RuntimeError
        with self.assertRaises(RuntimeError, msg="Should raise when API key missing"):
            claude_review.generate_review(SAMPLE_METADATA, SAMPLE_DIFF, [])

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("claude_review.anthropic.Anthropic")
    def test_generate_review_passes_diff_to_api(self, mock_anthropic):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_REVIEW)]
        mock_client.messages.create.return_value = mock_response

        claude_review.generate_review(SAMPLE_METADATA, SAMPLE_DIFF, [])

        call_kwargs = mock_client.messages.create.call_args[1]
        # The diff should appear in the user message
        user_content = call_kwargs["messages"][0]["content"]
        self.assertIn("user_id", user_content)

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"})
    @patch("claude_review.anthropic.Anthropic")
    def test_generate_review_truncates_large_diff(self, mock_anthropic):
        """Very large diffs should be truncated to 40k chars."""
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=SAMPLE_REVIEW)]
        mock_client.messages.create.return_value = mock_response

        huge_diff = "+" + "x" * 100_000
        claude_review.generate_review(SAMPLE_METADATA, huge_diff, [])

        call_kwargs = mock_client.messages.create.call_args[1]
        user_content = call_kwargs["messages"][0]["content"]
        self.assertLessEqual(len(user_content), 60_000)  # well under context limit


class TestCLIGuards(unittest.TestCase):
    """Tests for draft/closed PR guards in main()."""

    @patch("claude_review.get_pr_diff")
    @patch("claude_review.get_pr_metadata")
    def test_draft_pr_exits_cleanly(self, mock_meta, mock_diff):
        draft_meta = {**SAMPLE_METADATA, "isDraft": True}
        mock_meta.return_value = draft_meta

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.argv", ["prog", "42"]):
                claude_review.main()

        self.assertEqual(ctx.exception.code, 0)
        mock_diff.assert_not_called()

    @patch("claude_review.get_pr_diff")
    @patch("claude_review.get_pr_metadata")
    def test_closed_pr_exits_cleanly(self, mock_meta, mock_diff):
        closed_meta = {**SAMPLE_METADATA, "state": "CLOSED"}
        mock_meta.return_value = closed_meta

        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.argv", ["prog", "42"]):
                claude_review.main()

        self.assertEqual(ctx.exception.code, 0)
        mock_diff.assert_not_called()

    @patch("claude_review.get_pr_diff", return_value="")
    @patch("claude_review.get_pr_metadata", return_value=SAMPLE_METADATA)
    def test_empty_diff_exits_cleanly(self, mock_meta, mock_diff):
        with self.assertRaises(SystemExit) as ctx:
            with patch("sys.argv", ["prog", "42"]):
                claude_review.main()
        self.assertEqual(ctx.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
