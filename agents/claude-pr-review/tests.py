"""Tests for claude-review CLI."""
import importlib.util
import importlib.machinery
import sys
import os
import json
import tempfile
import unittest
import urllib.error
from unittest.mock import patch, MagicMock
from io import BytesIO

_path = os.path.join(os.path.dirname(__file__), "claude-review")
_loader = importlib.machinery.SourceFileLoader("claude_review", _path)
_spec = importlib.util.spec_from_loader("claude_review", _loader)
mod = importlib.util.module_from_spec(_spec)
_loader.exec_module(mod)

REVIEW_TEXT = (
    "## Summary\nThis PR adds feature X.\n\n"
    "## Identified Risks\n- None\n\n"
    "## Improvement Suggestions\n- Add tests\n\n"
    "## Confidence Score\n**High** — Small focused change.\n"
)

PR_META = {
    "title": "Add feature X",
    "user": {"login": "alice"},
    "base": {"label": "main"},
    "head": {"label": "alice:feature-x"},
    "changed_files": 3,
    "additions": 50,
    "deletions": 10,
    "body": "Adds feature X.",
}

DIFF = "diff --git a/foo.py b/foo.py\n+print('hello')\n"


def _mock_urlopen(text: str):
    payload = json.dumps({"content": [{"type": "text", "text": text}]}).encode()
    m = MagicMock()
    m.__enter__ = lambda s: BytesIO(payload)
    m.__exit__ = MagicMock(return_value=False)
    return m


class TestParsePrUrl(unittest.TestCase):
    def test_valid_url(self):
        owner, repo, num = mod.parse_pr_url("https://github.com/acme/myrepo/pull/42")
        self.assertEqual((owner, repo, num), ("acme", "myrepo", 42))

    def test_numeric_pr(self):
        _, _, num = mod.parse_pr_url("https://github.com/org/repo/pull/99")
        self.assertEqual(num, 99)

    def test_invalid_host_exits(self):
        with self.assertRaises(SystemExit):
            mod.parse_pr_url("https://gitlab.com/foo/bar/merge_requests/1")

    def test_non_pr_path_exits(self):
        with self.assertRaises(SystemExit):
            mod.parse_pr_url("https://github.com/foo/bar/issues/1")

    def test_no_number_exits(self):
        with self.assertRaises(SystemExit):
            mod.parse_pr_url("https://github.com/foo/bar/pull/")


class TestClaudeReview(unittest.TestCase):
    def test_all_four_sections_present(self):
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(REVIEW_TEXT)):
            result = mod.claude_review(PR_META, DIFF, "fake-key")
        for section in ("## Summary", "## Identified Risks", "## Improvement Suggestions", "## Confidence Score"):
            self.assertIn(section, result)

    def test_confidence_score_keyword(self):
        with patch("urllib.request.urlopen", return_value=_mock_urlopen(REVIEW_TEXT)):
            result = mod.claude_review(PR_META, DIFF, "fake-key")
        import re
        self.assertRegex(result, r"\*\*(Low|Medium|High)\*\*")

    def test_http_error_exits(self):
        err = urllib.error.HTTPError(None, 401, "Unauthorized", {}, BytesIO(b"bad key"))
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(SystemExit) as cm:
                mod.claude_review(PR_META, DIFF, "bad-key")
        self.assertIn("401", str(cm.exception))

    def test_url_error_exits(self):
        err = urllib.error.URLError("Connection refused")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(SystemExit) as cm:
                mod.claude_review(PR_META, DIFF, "fake-key")
        self.assertIn("Network error", str(cm.exception))

    def test_empty_content_exits(self):
        payload = json.dumps({"content": []}).encode()
        m = MagicMock()
        m.__enter__ = lambda s: BytesIO(payload)
        m.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=m):
            with self.assertRaises(SystemExit):
                mod.claude_review(PR_META, DIFF, "fake-key")


class TestGithubGet(unittest.TestCase):
    def test_returns_parsed_json(self):
        payload = json.dumps({"title": "Test PR"}).encode()
        m = MagicMock()
        m.__enter__ = lambda s: BytesIO(payload)
        m.__exit__ = MagicMock(return_value=False)
        with patch("urllib.request.urlopen", return_value=m):
            result = mod.github_get("/repos/foo/bar/pulls/1", token=None)
        self.assertEqual(result["title"], "Test PR")

    def test_http_error_exits(self):
        err = urllib.error.HTTPError(None, 404, "Not Found", {}, BytesIO(b"{}"))
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(SystemExit) as cm:
                mod.github_get("/repos/x/y/pulls/1", token=None)
        self.assertIn("404", str(cm.exception))

    def test_url_error_exits(self):
        err = urllib.error.URLError("timeout")
        with patch("urllib.request.urlopen", side_effect=err):
            with self.assertRaises(SystemExit):
                mod.github_get("/repos/x/y/pulls/1", token=None)


class TestMain(unittest.TestCase):
    def _mock_meta(self):
        return {**PR_META, "title": "Test PR"}

    def test_output_flag_writes_file(self):
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            outpath = f.name
        try:
            meta_payload = json.dumps(self._mock_meta()).encode()
            diff_payload = DIFF.encode()
            review_payload = json.dumps({"content": [{"type": "text", "text": REVIEW_TEXT}]}).encode()

            responses = [
                # github_get call
                MagicMock(**{"__enter__": lambda s: BytesIO(meta_payload), "__exit__": MagicMock(return_value=False)}),
                # github_diff call
                MagicMock(**{"__enter__": lambda s: BytesIO(diff_payload), "__exit__": MagicMock(return_value=False)}),
                # claude API call
                MagicMock(**{"__enter__": lambda s: BytesIO(review_payload), "__exit__": MagicMock(return_value=False)}),
            ]

            with patch("urllib.request.urlopen", side_effect=responses), \
                 patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake", "GITHUB_TOKEN": "fake"}), \
                 patch("sys.argv", ["claude-review", "--pr", "https://github.com/a/b/pull/1", "--output", outpath]):
                mod.main()

            content = open(outpath).read()
            self.assertIn("## Summary", content)
            self.assertIn("# Claude PR Review:", content)
        finally:
            os.unlink(outpath)

    def test_missing_api_key_exits(self):
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        with patch.dict(os.environ, env, clear=True), \
             patch("sys.argv", ["claude-review", "--pr", "https://github.com/a/b/pull/1"]):
            with self.assertRaises(SystemExit):
                mod.main()

    def test_post_comment_without_token_exits(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake"}, clear=True), \
             patch("sys.argv", ["claude-review", "--pr", "https://github.com/a/b/pull/1",
                                "--post-comment"]):
            with self.assertRaises(SystemExit) as cm:
                mod.main()
        self.assertIn("GITHUB_TOKEN", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
