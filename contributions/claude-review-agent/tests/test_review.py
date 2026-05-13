"""Tests for claude-review."""

import pytest

from claude_review.github_client import parse_pr_url


class TestParsePRUrl:
    def test_full_url(self):
        owner, repo, num = parse_pr_url("https://github.com/facebook/react/pull/28000")
        assert owner == "facebook"
        assert repo == "react"
        assert num == 28000

    def test_short_format(self):
        owner, repo, num = parse_pr_url("owner/repo#42")
        assert owner == "owner"
        assert repo == "repo"
        assert num == 42

    def test_invalid_url(self):
        with pytest.raises(ValueError):
            parse_pr_url("not-a-valid-url")

    def test_http_url(self):
        owner, repo, num = parse_pr_url("http://github.com/org/project/pull/1")
        assert owner == "org"
        assert repo == "project"
        assert num == 1


class TestReviewerParsing:
    """Test response parsing without API calls."""

    def test_parse_structured_response(self):
        from claude_review.reviewer import Reviewer

        reviewer = Reviewer.__new__(Reviewer)
        text = """### Summary
This PR adds a new feature for user authentication.

### Risks
- No input validation on email field
- Missing rate limiting

### Suggestions
- Add email format validation
- Implement rate limiting middleware

### Confidence
**Medium**
"""
        result = reviewer._parse_response(text)
        assert "authentication" in result.summary
        assert len(result.risks) == 2
        assert len(result.suggestions) == 2
        assert result.confidence == "Medium"

    def test_parse_high_confidence(self):
        from claude_review.reviewer import Reviewer

        reviewer = Reviewer.__new__(Reviewer)
        text = """### Summary
Simple typo fix.

### Risks
- No significant risks identified.

### Suggestions
- No suggestions — looks good!

### Confidence
**High**
"""
        result = reviewer._parse_response(text)
        assert result.confidence == "High"
