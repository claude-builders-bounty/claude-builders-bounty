import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple


class PRFetchError(Exception):
    """Raised when PR metadata or diff cannot be retrieved."""
    pass


def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
    """
    Extracts (owner, repo, pr_number) from a GitHub pull request URL.
    Supports formats like:
      - https://github.com/owner/repo/pull/123
      - github.com/owner/repo/pull/123
    """
    pattern = r"github\.com[/:](?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        raise ValueError(
            f"Invalid GitHub PR URL format: '{pr_url}'. "
            "Expected: https://github.com/<owner>/<repo>/pull/<number>"
        )
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def fetch_pr_details(
    pr_url: str,
    token: str = None
) -> Tuple[Dict[str, Any], str]:
    """
    Fetches PR metadata and unified diff from GitHub REST API.
    Returns:
        (metadata_dict, diff_text)
    """
    owner, repo, pr_number = parse_pr_url(pr_url)
    auth_token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    headers = {
        "User-Agent": "Claude-Code-PR-Review-Agent/1.0",
        "Accept": "application/vnd.github.v3+json",
    }
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"

    base_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    # 1. Fetch PR Metadata
    try:
        req_meta = urllib.request.Request(base_api_url, headers=headers)
        with urllib.request.urlopen(req_meta, timeout=15) as resp:
            metadata = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_msg = f"HTTP {e.code}: {e.reason}"
        if e.code == 404:
            error_msg += " (PR not found or repository is private; provide a GITHUB_TOKEN)"
        elif e.code == 403:
            error_msg += " (API rate limit exceeded or access forbidden)"
        raise PRFetchError(f"Failed to fetch PR metadata from {base_api_url}: {error_msg}") from e
    except Exception as e:
        raise PRFetchError(f"Network error fetching PR metadata: {e}") from e

    # 2. Fetch PR Diff
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"

    try:
        req_diff = urllib.request.Request(base_api_url, headers=diff_headers)
        with urllib.request.urlopen(req_diff, timeout=20) as resp:
            diff_text = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        raise PRFetchError(f"Failed to fetch PR diff from {base_api_url}: {e}") from e

    return metadata, diff_text


def post_pr_comment(
    pr_url: str,
    comment_body: str,
    token: str = None
) -> str:
    """
    Posts a review comment to the specified pull request.
    Returns the created comment URL.
    """
    owner, repo, pr_number = parse_pr_url(pr_url)
    auth_token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not auth_token:
        raise PRFetchError("Cannot post PR comment: GITHUB_TOKEN is required.")

    comments_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    headers = {
        "User-Agent": "Claude-Code-PR-Review-Agent/1.0",
        "Authorization": f"Bearer {auth_token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    payload = json.dumps({"body": comment_body}).encode("utf-8")

    try:
        req = urllib.request.Request(comments_url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            return res_data.get("html_url", "")
    except Exception as e:
        raise PRFetchError(f"Failed to post comment to {comments_url}: {e}") from e
