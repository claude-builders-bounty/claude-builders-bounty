"""
Tests for confidence scoring logic
These tests should FAIL initially, then PASS after implementation
"""

import pytest
import sys
sys.path.insert(0, '..')


class TestConfidenceScoring:
    """Test confidence score calculation"""

    def test_high_confidence_small_pr(self):
        """Test high confidence for small, clean PR"""
        from claude_pr_review import calculate_confidence

        pr_data = {
            "files_changed": 2,
            "additions": 50,
            "deletions": 20,
            "has_tests": True,
            "security_issues": []
        }

        confidence = calculate_confidence(pr_data)
        assert confidence == "HIGH"

    def test_medium_confidence_moderate_pr(self):
        """Test medium confidence for moderate complexity PR"""
        from claude_pr_review import calculate_confidence

        pr_data = {
            "files_changed": 8,
            "additions": 300,
            "deletions": 100,
            "has_tests": True,
            "security_issues": ["warning"]
        }

        confidence = calculate_confidence(pr_data)
        assert confidence == "MEDIUM"

    def test_low_confidence_large_pr(self):
        """Test low confidence for large, complex PR"""
        from claude_pr_review import calculate_confidence

        pr_data = {
            "files_changed": 15,
            "additions": 800,
            "deletions": 300,
            "has_tests": False,
            "security_issues": ["critical", "warning"]
        }

        confidence = calculate_confidence(pr_data)
        assert confidence == "LOW"

    def test_confidence_with_no_tests(self):
        """Test confidence reduction when no tests"""
        from claude_pr_review import calculate_confidence

        pr_data_with_tests = {
            "files_changed": 3,
            "additions": 100,
            "deletions": 50,
            "has_tests": True,
            "security_issues": []
        }

        pr_data_no_tests = {
            "files_changed": 3,
            "additions": 100,
            "deletions": 50,
            "has_tests": False,
            "security_issues": []
        }

        confidence_with = calculate_confidence(pr_data_with_tests)
        confidence_without = calculate_confidence(pr_data_no_tests)

        # Confidence should be lower without tests
        confidence_map = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        assert confidence_map[confidence_without] < confidence_map[confidence_with]


class TestReviewVerdict:
    """Test review verdict determination"""

    def test_approve_verdict(self):
        """Test APPROVE verdict for clean PR"""
        from claude_pr_review import determine_verdict

        review_data = {
            "security_issues": [],
            "code_quality_issues": [],
            "confidence": "HIGH"
        }

        verdict = determine_verdict(review_data)
        assert verdict == "APPROVE"

    def test_request_changes_verdict(self):
        """Test REQUEST_CHANGES verdict for PR with critical issues"""
        from claude_pr_review import determine_verdict

        review_data = {
            "security_issues": ["CRITICAL: API key exposed"],
            "code_quality_issues": [],
            "confidence": "MEDIUM"
        }

        verdict = determine_verdict(review_data)
        assert verdict == "REQUEST_CHANGES"

    def test_comment_verdict(self):
        """Test COMMENT verdict for PR with minor issues"""
        from claude_pr_review import determine_verdict

        review_data = {
            "security_issues": [],
            "code_quality_issues": ["Consider adding type hints"],
            "confidence": "HIGH"
        }

        verdict = determine_verdict(review_data)
        assert verdict == "COMMENT"
