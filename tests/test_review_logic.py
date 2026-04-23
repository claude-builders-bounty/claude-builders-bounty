"""
Tests for Claude API review generation
These tests should FAIL initially, then PASS after implementation
"""

import pytest
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, '..')


class TestReviewGeneration:
    """Test Claude API review generation"""

    def test_generate_review_structure(self):
        """Test that generated review has required sections"""
        from claude_pr_review import generate_review

        mock_response = """
## Summary
This PR adds user authentication.

### Security Analysis
- No issues found

### Code Quality
- Good separation of concerns

### Improvement Suggestions
1. Add more tests
"""

        with patch('claude_pr_review.call_claude_api') as mock_claude:
            mock_claude.return_value = mock_response

            review = generate_review("fake_diff", {"title": "Test"}, "fake_key")

            assert "## Summary" in review
            assert "Security Analysis" in review
            assert "Code Quality" in review
            assert "Improvement Suggestions" in review

    def test_review_includes_metadata(self):
        """Test that review includes PR metadata"""
        from claude_pr_review import format_review

        metadata = {
            "number": 123,
            "title": "Add feature",
            "author": "testuser",
            "files_changed": 5,
            "additions": 234,
            "deletions": 56
        }

        review_content = "This is a review"

        formatted = format_review(review_content, metadata, confidence="HIGH", verdict="APPROVE")

        assert "#123" in formatted
        assert "Add feature" in formatted
        assert "@testuser" in formatted
        assert "5" in formatted  # files changed

    def test_review_includes_cost(self):
        """Test that review includes cost tracking"""
        from claude_pr_review import format_review

        metadata = {"number": 123, "title": "Test"}
        review_content = "Review"

        formatted = format_review(
            review_content, metadata,
            confidence="HIGH", verdict="APPROVE",
            tokens_used=1234, cost=0.025
        )

        assert "1234" in formatted or "1,234" in formatted
        assert "$0.025" in formatted or "$0.03" in formatted


class TestPromptEngineering:
    """Test Claude prompt construction"""

    def test_build_review_prompt(self):
        """Test that review prompt includes necessary context"""
        from claude_pr_review import build_review_prompt

        diff = "sample diff content"
        metadata = {
            "title": "Add auth",
            "author": "testuser"
        }

        prompt = build_review_prompt(diff, metadata)

        # Prompt should include instructions
        assert "review" in prompt.lower()
        assert "security" in prompt.lower()
        assert "quality" in prompt.lower()

        # Prompt should include context
        assert "Add auth" in prompt
        assert "sample diff content" in prompt

    def test_prompt_has_output_format(self):
        """Test that prompt specifies desired output format"""
        from claude_pr_review import build_review_prompt

        prompt = build_review_prompt("diff", {})

        # Should specify markdown format
        assert "markdown" in prompt.lower() or "##" in prompt
        # Should ask for specific sections
        assert "summary" in prompt.lower()
