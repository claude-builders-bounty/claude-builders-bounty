import pytest
from claude_review.pr_fetcher import parse_pr_url, PRFetchError


def test_parse_pr_url_valid():
    owner, repo, number = parse_pr_url("https://github.com/fastapi/fastapi/pull/1234")
    assert owner == "fastapi"
    assert repo == "fastapi"
    assert number == 1234


def test_parse_pr_url_git_domain():
    owner, repo, number = parse_pr_url("github.com/facebook/react/pull/999")
    assert owner == "facebook"
    assert repo == "react"
    assert number == 999


def test_parse_pr_url_invalid():
    with pytest.raises(ValueError):
        parse_pr_url("https://gitlab.com/owner/repo/pull/123")

    with pytest.raises(ValueError):
        parse_pr_url("https://github.com/owner/repo/issues/123")
