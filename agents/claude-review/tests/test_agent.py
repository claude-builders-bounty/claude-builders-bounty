"""Tests for Claude Review Agent."""

import pytest
from claude_review.agent import PRReviewer, PRData, ReviewResult
from claude_review.formatter import format_review, format_review_compact


class TestPRReviewer:
    """Tests for PRReviewer class."""
    
    def test_parse_pr_url_standard(self):
        """Test parsing standard GitHub PR URL."""
        reviewer = PRReviewer()
        owner, repo, number = reviewer._parse_pr_url(
            "https://github.com/owner/repo/pull/123"
        )
        assert owner == "owner"
        assert repo == "repo"
        assert number == 123
    
    def test_parse_pr_url_with_trailing_slash(self):
        """Test parsing PR URL with trailing slash."""
        reviewer = PRReviewer()
        owner, repo, number = reviewer._parse_pr_url(
            "https://github.com/owner/repo/pull/123/"
        )
        assert owner == "owner"
        assert repo == "repo"
        assert number == 123
    
    def test_parse_pr_url_invalid(self):
        """Test parsing invalid PR URL."""
        reviewer = PRReviewer()
        with pytest.raises(ValueError):
            reviewer._parse_pr_url("https://example.com/owner/repo/pull/123")
    
    def test_generate_summary(self):
        """Test summary generation."""
        reviewer = PRReviewer()
        pr_data = PRData(
            title="Add new feature",
            body="This adds a new feature",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="+++ b/feature.py\n+def new_feature():\n+    pass",
            files_changed=1,
            additions=3,
            deletions=0
        )
        
        summary = reviewer._generate_summary(pr_data)
        assert "Add new feature" in summary
        assert "+3" in summary
    
    def test_identify_risks_hardcoded_password(self):
        """Test risk identification for hardcoded passwords."""
        reviewer = PRReviewer()
        pr_data = PRData(
            title="Update config",
            body="",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="password = 'secret123'",
            files_changed=1,
            additions=1,
            deletions=0
        )
        
        risks = reviewer._identify_risks(pr_data)
        assert any("password" in risk.lower() for risk in risks)
    
    def test_identify_risks_no_risks(self):
        """Test when no risks are identified."""
        reviewer = PRReviewer()
        pr_data = PRData(
            title="Simple update",
            body="Updates documentation",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="+++ b/README.md\n+Updated docs",
            files_changed=1,
            additions=1,
            deletions=0
        )
        
        risks = reviewer._identify_risks(pr_data)
        assert len(risks) > 0  # Should have at least "no significant risks"
    
    def test_calculate_confidence_high(self):
        """Test confidence calculation - high."""
        reviewer = PRReviewer()
        pr_data = PRData(
            title="Good PR",
            body="Detailed description",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="simple changes",
            files_changed=1,
            additions=10,
            deletions=5
        )
        
        confidence = reviewer._calculate_confidence(pr_data, [])
        assert confidence in ["High", "Medium"]
    
    def test_calculate_confidence_low(self):
        """Test confidence calculation - low."""
        reviewer = PRReviewer()
        pr_data = PRData(
            title="Risky PR",
            body="",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="password = 'secret' and eval(user_input)",
            files_changed=1,
            additions=100,
            deletions=50
        )
        
        risks = ["Potential hardcoded password", "Use of eval/exec"]
        confidence = reviewer._calculate_confidence(pr_data, risks)
        assert confidence in ["Low", "Medium"]


class TestFormatter:
    """Tests for formatter functions."""
    
    def test_format_review(self):
        """Test full review formatting."""
        pr_data = PRData(
            title="Test PR",
            body="Test body",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="test diff",
            files_changed=1,
            additions=10,
            deletions=5
        )
        
        result = ReviewResult(
            summary="Test summary",
            risks=["Risk 1", "Risk 2"],
            suggestions=["Suggestion 1"],
            confidence="High"
        )
        
        output = format_review(pr_data, result)
        
        assert "## Summary" in output
        assert "Test summary" in output
        assert "## Identified Risks" in output
        assert "Risk 1" in output
        assert "## Improvement Suggestions" in output
        assert "Suggestion 1" in output
        assert "## Confidence Score" in output
        assert "High" in output
    
    def test_format_review_compact(self):
        """Test compact review formatting."""
        pr_data = PRData(
            title="Test PR",
            body="Test body",
            author="testuser",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="test diff",
            files_changed=1,
            additions=10,
            deletions=5
        )
        
        result = ReviewResult(
            summary="Test summary",
            risks=["Risk 1"],
            suggestions=["Suggestion 1"],
            confidence="Medium"
        )
        
        output = format_review_compact(pr_data, result)
        
        assert "## 🤖 Claude Review Agent" in output
        assert "Medium" in output
        assert "### Summary" in output
        assert "### Risks" in output
        assert "### Suggestions" in output


class TestPRData:
    """Tests for PRData dataclass."""
    
    def test_pr_data_creation(self):
        """Test PRData creation."""
        pr_data = PRData(
            title="Test",
            body="Body",
            author="user",
            repo="owner/repo",
            number=1,
            url="https://github.com/owner/repo/pull/1",
            diff="diff"
        )
        
        assert pr_data.title == "Test"
        assert pr_data.author == "user"
        assert pr_data.number == 1
        assert pr_data.files_changed == 0
        assert pr_data.additions == 0
        assert pr_data.deletions == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
