"""
Unit tests for Claude PR Reviewer Agent (#4).
"""

import pytest
import sys
from pathlib import Path

# Add package root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from claude_review.reviewer import ClaudePRReviewer, ReviewResult

class TestClaudePRReviewer:
    def test_parse_pr_url_valid(self):
        urls = [
            ("https://github.com/facebook/react/pull/12345", ("facebook", "react", 12345)),
            ("https://github.com/owner-org/repo.name/pull/42/", ("owner-org", "repo.name", 42)),
            ("http://github.com/user/project/pull/1", ("user", "project", 1))
        ]
        for url, expected in urls:
            assert ClaudePRReviewer.parse_pr_url(url) == expected

    def test_parse_pr_url_invalid(self):
        with pytest.raises(ValueError):
            ClaudePRReviewer.parse_pr_url("https://github.com/owner/repo/issues/123")

        with pytest.raises(ValueError):
            ClaudePRReviewer.parse_pr_url("https://notgithub.com/owner/repo/pull/123")

    def test_analyze_diff_structured_markdown(self):
        reviewer = ClaudePRReviewer()
        diff = """
diff --git a/src/auth.py b/src/auth.py
--- a/src/auth.py
+++ b/src/auth.py
@@ -10,3 +10,5 @@
+def secure_verify_token(token: str) -> bool:
+    return len(token) > 32
"""
        result = reviewer.analyze_diff("testowner", "testrepo", 101, "feat: secure auth", diff)
        assert isinstance(result, ReviewResult)
        assert result.owner == "testowner"
        assert result.repo == "testrepo"
        assert result.pr_number == 101
        assert len(result.summary) > 0
        assert len(result.risks) >= 1
        assert len(result.suggestions) >= 1
        assert result.confidence in ["Low", "Medium", "High"]
        assert result.recommendation in ["APPROVE", "REQUEST_CHANGES", "COMMENT"]
        assert "## 🤖 Claude Code Automated PR Review" in result.markdown_output

    def test_analyze_diff_flag_secrets(self):
        reviewer = ClaudePRReviewer()
        diff = """
diff --git a/config.py b/config.py
+++ b/config.py
+SECRET_API_KEY = "sk-1234567890abcdef"
"""
        result = reviewer.analyze_diff("testowner", "testrepo", 102, "chore: add keys", diff)
        assert result.recommendation == "REQUEST_CHANGES"
        assert any("secret" in r.lower() or "credential" in r.lower() for r in result.risks)

    def test_custom_mock_claude_response(self):
        reviewer = ClaudePRReviewer()
        mock_output = """## 🤖 Claude Code Automated PR Review

### 📝 Summary of Changes
This pull request refactors the cache invalidation logic across Redis and local memory stores. It eliminates deadlock potential.

### ⚠️ Identified Risks
- Race condition on simultaneous TTL expiration.
- Memory pressure on large cluster deployments.

### 💡 Improvement Suggestions
- Introduce exponential backoff on cache misses.
- Add OpenTelemetry metrics for cache hit ratio.

### 🎯 Recommendation & Confidence
- **Recommendation**: APPROVE
- **Confidence Score**: High
- **Rationale**: Clean decoupled implementation with extensive unit coverage.
"""
        mock_fn = lambda prompt: mock_output
        result = reviewer.analyze_diff("testowner", "testrepo", 200, "refactor cache", "dummy diff", mock_client=mock_fn)
        assert result.recommendation == "APPROVE"
        assert result.confidence == "High"
        assert len(result.risks) == 2
        assert len(result.suggestions) == 2
        assert "Redis" in result.summary
