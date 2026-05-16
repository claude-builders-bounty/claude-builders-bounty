"""Tests for claude-review CLI tool"""
import pytest
from claude_review import parse_pr_url

class TestClaudeReview:
    def test_parse_standard_url(self):
        owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/123")
        assert owner == "owner"
        assert repo == "repo"
        assert num == 123

    def test_parse_url_with_trailing_slash(self):
        owner, repo, num = parse_pr_url("https://github.com/a/b/pull/456/")
        assert owner == "a"
        assert repo == "b"
        assert num == 456

    def test_parse_invalid_url_raises(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://gitlab.com/owner/repo/merge_requests/1")

    def test_parse_not_a_pr_url(self):
        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo/issues/1")

    def test_parse_missing_protocol(self):
        # Should work since we use re.match which finds pattern anywhere
        owner, repo, num = parse_pr_url("github.com/x/y/pull/789")
        assert num == 789
