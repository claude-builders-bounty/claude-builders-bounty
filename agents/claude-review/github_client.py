"""
GitHub Client for Claude Review Agent.
Handles PR URL parsing, diff fetching, metadata extraction, and comment posting.
"""

import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional


def parse_pr_url(url_or_ref: str) -> Tuple[str, str, int]:
    """
    Parses GitHub PR URL or shorthand reference into (owner, repo, pr_number).
    Supported formats:
      - https://github.com/owner/repo/pull/123
      - http://github.com/owner/repo/pull/123
      - owner/repo#123
      - owner/repo/pull/123
    """
    url_or_ref = url_or_ref.strip()

    # Pattern 1: standard URL
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url_or_ref)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    # Pattern 2: owner/repo#123
    match = re.match(r"^([^/]+)/([^#]+)#(\d+)$", url_or_ref)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    # Pattern 3: owner/repo/pull/123
    match = re.match(r"^([^/]+)/([^/]+)/pull/(\d+)$", url_or_ref)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    raise ValueError(
        f"Invalid GitHub Pull Request reference '{url_or_ref}'. "
        "Expected format: https://github.com/owner/repo/pull/<number> or owner/repo#<number>"
    )


def _build_request(url: str, token: Optional[str] = None, accept: str = "application/json", data: Optional[bytes] = None) -> urllib.request.Request:
    """Builds an authenticated urllib Request object."""
    req = urllib.request.Request(url, data=data)
    req.add_header("Accept", accept)
    req.add_header("User-Agent", "Claude-Code-PR-Reviewer/1.0")

    auth_token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if auth_token:
        req.add_header("Authorization", f"Bearer {auth_token}")

    return req


def fetch_pr_diff(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> str:
    """
    Fetches the raw unified diff for a GitHub pull request.
    Uses the GitHub REST API endpoint with the diff media type.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = _build_request(url, token=token, accept="application/vnd.github.v3.diff")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 404:
            raise RuntimeError(
                f"PR #{pr_number} not found on {owner}/{repo}. Check URL and permissions."
            ) from e
        elif e.code == 403 and "API rate limit exceeded" in body:
            raise RuntimeError(
                "GitHub API rate limit exceeded. Provide a personal access token via --token or GITHUB_TOKEN."
            ) from e
        raise RuntimeError(f"GitHub API error ({e.code}): {body}") from e
    except Exception as e:
        raise RuntimeError(f"Network error while fetching PR diff: {e}") from e


def fetch_pr_metadata(owner: str, repo: str, pr_number: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetches PR details (title, description, author, branch targets, stats).
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = _build_request(url, token=token, accept="application/vnd.github.v3+json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Fallback to empty metadata if unauthenticated or rate limited
        return {
            "title": f"PR #{pr_number}",
            "body": "",
            "html_url": f"https://github/{owner}/{repo}/pull/{pr_number}",
            "user": {"login": "unknown"},
            "head": {"ref": "feature"},
            "base": {"ref": "main"}
        }


def post_pr_comment(owner: str, repo: str, pr_number: int, comment_body: str, token: Optional[str] = None) -> str:
    """
    Posts a review markdown comment to a GitHub PR issue thread.
    Returns the posted comment URL.
    """
    auth_token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not auth_token:
        raise ValueError(
            "Cannot post comment: No GitHub token provided. "
            "Please supply --token or export GITHUB_TOKEN."
        )

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    req = _build_request(url, token=auth_token, accept="application/vnd.github.v3+json", data=payload)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("html_url", url)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Failed to post PR comment ({e.code}): {body}") from e
