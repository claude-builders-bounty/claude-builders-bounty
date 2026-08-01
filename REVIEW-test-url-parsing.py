"""Tests for claude-review URL parsing."""
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent))

import importlib.util
import sys
from pathlib import Path

# Load claude-review.py dynamically (has a hyphen, can't import normally)
spec = importlib.util.spec_from_file_location("claude_review", Path(__file__).parent / "claude-review.py")
claude_review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(claude_review)
parse_pr_url = claude_review.parse_pr_url


def test_full_https_url():
    owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/123")
    assert owner == "owner"
    assert repo == "repo"
    assert num == 123
    print("  ✅ full https URL")


def test_full_http_url():
    owner, repo, num = parse_pr_url("http://github.com/owner/repo/pull/456")
    assert owner == "owner"
    assert repo == "repo"
    assert num == 456
    print("  ✅ full http URL")


def test_url_with_trailing_slash():
    owner, repo, num = parse_pr_url("https://github.com/owner/repo/pull/789/")
    assert owner == "owner"
    assert repo == "repo"
    assert num == 789
    print("  ✅ URL with trailing slash")


def test_short_form():
    owner, repo, num = parse_pr_url("owner/repo#123")
    assert owner == "owner"
    assert repo == "repo"
    assert num == 123
    print("  ✅ short form (owner/repo#num)")


def test_invalid_url():
    try:
        parse_pr_url("not a url")
        assert False, "should have raised"
    except ValueError:
        print("  ✅ invalid URL raises ValueError")


def test_invalid_short_form():
    try:
        parse_pr_url("just-a-name")
        assert False, "should have raised"
    except ValueError:
        print("  ✅ invalid short form raises ValueError")


if __name__ == "__main__":
    print("=== URL parsing tests ===")
    test_full_https_url()
    test_full_http_url()
    test_url_with_trailing_slash()
    test_short_form()
    test_invalid_url()
    test_invalid_short_form()
    print("\n✅ All tests pass.")
