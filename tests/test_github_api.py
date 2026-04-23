"""
Tests for GitHub API integration
These tests should FAIL initially, then PASS after implementation
"""

import pytest
from unittest.mock import Mock, patch
import sys
sys.path.insert(0, '..')


class TestGitHubAPI:
    """Test GitHub API diff fetching"""

    def test_parse_pr_url(self):
        """Test parsing PR URL into owner/repo/number"""
        from claude_pr_review import parse_pr_url

        url = "https://github.com/owner/repo/pull/123"
        owner, repo, pr_number = parse_pr_url(url)

        assert owner == "owner"
        assert repo == "repo"
        assert pr_number == 123

    def test_parse_pr_url_invalid(self):
        """Test error handling for invalid PR URL"""
        from claude_pr_review import parse_pr_url

        with pytest.raises(ValueError):
            parse_pr_url("https://github.com/owner/repo")

    def test_fetch_pr_diff(self):
        """Test fetching PR diff from GitHub API"""
        from claude_pr_review import fetch_pr_diff

        # Mock GitHub API response
        mock_diff = """
diff --git a/file.py b/file.py
index abc123..def456 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
+# New line
 def hello():
     print("world")
"""

        with patch('claude_pr_review.github_api_request') as mock_api:
            mock_api.return_value = mock_diff

            diff = fetch_pr_diff("owner", "repo", 123, "fake_token")

            assert "New line" in diff
            assert "def hello" in diff

    def test_fetch_pr_metadata(self):
        """Test fetching PR metadata (title, author, files changed)"""
        from claude_pr_review import fetch_pr_metadata

        mock_pr_data = {
            "title": "Add feature",
            "user": {"login": "author"},
            "additions": 234,
            "deletions": 56,
            "changed_files": 5
        }

        with patch('claude_pr_review.github_api_request') as mock_api:
            mock_api.return_value = mock_pr_data

            metadata = fetch_pr_metadata("owner", "repo", 123, "fake_token")

            assert metadata["title"] == "Add feature"
            assert metadata["author"] == "author"
            assert metadata["files_changed"] == 5


class TestErrorHandling:
    """Test error handling for GitHub API"""

    def test_handle_rate_limit(self):
        """Test handling GitHub API rate limit"""
        from claude_pr_review import fetch_pr_diff

        with patch('claude_pr_review.github_api_request') as mock_api:
            mock_api.side_effect = Exception("API rate limit exceeded")

            with pytest.raises(Exception) as exc_info:
                fetch_pr_diff("owner", "repo", 123, "fake_token")

            assert "rate limit" in str(exc_info.value).lower()

    def test_handle_pr_not_found(self):
        """Test handling PR not found (404)"""
        from claude_pr_review import fetch_pr_diff

        with patch('claude_pr_review.github_api_request') as mock_api:
            mock_api.side_effect = Exception("404 Not Found")

            with pytest.raises(Exception) as exc_info:
                fetch_pr_diff("owner", "repo", 999, "fake_token")

            assert "404" in str(exc_info.value)
