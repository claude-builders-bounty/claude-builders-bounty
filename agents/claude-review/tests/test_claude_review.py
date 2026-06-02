"""
Tests for claude_review.py

Run with: python -m pytest tests/test_claude_review.py -v
"""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add parent dir to path so we can import the module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_review import (
    MODEL,
    REVIEW_SYSTEM_PROMPT,
    _parse_pr_url,
    build_parser,
    call_claude,
    fetch_pr_diff,
    fetch_pr_metadata,
    main,
    read_local_diff,
)


# ── _parse_pr_url ──────────────────────────────────────────────────────────────


class TestParsePrUrl:
    def test_standard_url(self):
        owner, repo, num = _parse_pr_url("https://github.com/owner/repo/pull/123")
        assert owner == "owner"
        assert repo == "repo"
        assert num == "123"

    def test_url_with_trailing_slash(self):
        owner, repo, num = _parse_pr_url("https://github.com/owner/repo/pull/456/")
        assert owner == "owner"
        assert repo == "repo"
        assert num == "456"

    def test_url_with_files(self):
        owner, repo, num = _parse_pr_url("https://github.com/owner/repo/pull/789/files")
        assert owner == "owner"
        assert repo == "repo"
        assert num == "789"

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Cannot parse PR URL"):
            _parse_pr_url("https://example.com/not-a-pr")

    def test_issue_url_raises(self):
        with pytest.raises(ValueError, match="Cannot parse PR URL"):
            _parse_pr_url("https://github.com/owner/repo/issues/5")


# ── read_local_diff ────────────────────────────────────────────────────────────


class TestReadLocalDiff:
    def test_reads_existing_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write("diff --git a/foo b/foo\n+hello\n")
            path = f.name
        try:
            diff = read_local_diff(path)
            assert "diff --git" in diff
            assert "+hello" in diff
        finally:
            os.unlink(path)

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            read_local_diff("/nonexistent/path.diff")

    def test_large_diff_truncated(self):
        # Create a file larger than MAX_DIFF_CHARS
        from claude_review import MAX_DIFF_CHARS

        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write("x" * (MAX_DIFF_CHARS + 1000))
            path = f.name
        try:
            diff = read_local_diff(path)
            assert len(diff) < MAX_DIFF_CHARS + 1000
            assert "truncated" in diff
        finally:
            os.unlink(path)


# ── fetch_pr_diff ──────────────────────────────────────────────────────────────


class TestFetchPrDiff:
    @patch("claude_review._run_cmd")
    def test_calls_gh_api(self, mock_run):
        mock_result = MagicMock()
        mock_result.stdout = "diff --git a/foo b/foo\n+added line\n"
        mock_run.return_value = mock_result

        diff = fetch_pr_diff("owner", "repo", "42")
        assert "diff --git" in diff
        mock_run.assert_called_once()

    @patch("claude_review._run_cmd")
    def test_truncates_large_diff(self, mock_run):
        from claude_review import MAX_DIFF_CHARS

        mock_result = MagicMock()
        mock_result.stdout = "x" * (MAX_DIFF_CHARS + 500)
        mock_run.return_value = mock_result

        diff = fetch_pr_diff("owner", "repo", "42")
        assert "truncated" in diff


# ── fetch_pr_metadata ──────────────────────────────────────────────────────────


class TestFetchPrMetadata:
    def test_returns_metadata(self):
        with patch("claude_review._run_cmd") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = json.dumps({
                "title": "Test PR",
                "user": {"login": "testuser"},
                "additions": 10,
                "deletions": 5,
                "changed_files": 2,
                "html_url": "https://github.com/owner/repo/pull/1",
            })
            mock_run.return_value = mock_result

            meta = fetch_pr_metadata("owner", "repo", "1")
            assert meta["title"] == "Test PR"
            assert meta["author"] == "testuser"
            assert meta["additions"] == 10

    def test_handles_error(self):
        with patch("claude_review._run_cmd", side_effect=Exception("API error")):
            meta = fetch_pr_metadata("owner", "repo", "1")
            assert meta["title"] == "Unknown"


# ── call_claude ────────────────────────────────────────────────────────────────


class TestCallClaude:
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-123"})
    @patch("claude_review._run_cmd")
    def test_curl_fallback(self, mock_run):
        """Test curl fallback when anthropic SDK is not importable."""
        # This test exercises the curl path by mocking _run_cmd
        # (anthropic SDK import will fail in test env or succeed — either way is fine)
        try:
            import anthropic

            # If anthropic is installed, we need to mock the client
            with patch("anthropic.Anthropic") as mock_client_cls:
                mock_client = MagicMock()
                mock_client_cls.return_value = mock_client
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text="## 📋 Change Summary\nTest review")]
                mock_client.messages.create.return_value = mock_response

                result = call_claude("diff content")
                assert "Change Summary" in result
        except ImportError:
            # anthropic not installed — curl fallback path
            mock_result = MagicMock()
            mock_result.stdout = json.dumps({
                "content": [{"text": "## 📋 Change Summary\nTest review from curl"}]
            })
            mock_run.return_value = mock_result

            result = call_claude("diff content")
            assert "Change Summary" in result

    def test_missing_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            # Remove ANTHROPIC_API_KEY if it exists
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises((SystemExit, RuntimeError)):
                call_claude("diff content")


# ── build_parser ───────────────────────────────────────────────────────────────


class TestBuildParser:
    def test_pr_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--pr", "https://github.com/o/r/pull/1"])
        assert args.pr == "https://github.com/o/r/pull/1"

    def test_diff_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--diff", "patch.diff"])
        assert args.diff == "patch.diff"

    def test_output_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--pr", "https://github.com/o/r/pull/1", "-o", "out.md"])
        assert args.output == "out.md"

    def test_post_flag(self):
        parser = build_parser()
        args = parser.parse_args(["--pr", "https://github.com/o/r/pull/1", "--post"])
        assert args.post is True

    def test_pr_and_diff_mutually_exclusive(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["--pr", "url", "--diff", "file"])

    def test_requires_either_pr_or_diff(self):
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])


# ── Integration-style test (mocked) ───────────────────────────────────────────


class TestMainIntegration:
    @patch("claude_review.call_claude")
    @patch("claude_review.fetch_pr_metadata")
    @patch("claude_review.fetch_pr_diff")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"})
    def test_main_with_pr_url(self, mock_diff, mock_meta, mock_claude, capsys):
        mock_diff.return_value = "diff --git a/foo b/foo\n+added\n"
        mock_meta.return_value = {
            "title": "Test PR",
            "author": "testuser",
            "additions": 5,
            "deletions": 2,
            "changed_files": 1,
            "url": "https://github.com/o/r/pull/1",
            "pr_number": "1",
        }
        mock_claude.return_value = "## 📋 Change Summary\nTest review\n\n## 🏆 Code Quality Score: 8/10\nGood code."

        with patch("sys.argv", ["claude-review", "--pr", "https://github.com/o/r/pull/1"]):
            main()

        captured = capsys.readouterr()
        assert "Change Summary" in captured.out
        assert "Code Quality Score" in captured.out

    @patch("claude_review.call_claude")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"})
    def test_main_with_local_diff(self, mock_claude, capsys):
        mock_claude.return_value = "## 📋 Change Summary\nLocal diff review\n\n## 🏆 Code Quality Score: 7/10\nDecent."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write("diff --git a/bar b/bar\n+new line\n")
            path = f.name

        try:
            with patch("sys.argv", ["claude-review", "--diff", path]):
                main()

            captured = capsys.readouterr()
            assert "Change Summary" in captured.out
        finally:
            os.unlink(path)
