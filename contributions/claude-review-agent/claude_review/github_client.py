"""GitHub API client for fetching PR data."""

import os
import re
from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class PRData:
    """Structured pull request data."""
    owner: str
    repo: str
    number: int
    title: str
    body: str
    diff: str
    files_changed: int
    additions: int
    deletions: int
    base_branch: str
    head_branch: str
    author: str
    url: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Extract owner, repo, and PR number from a GitHub PR URL.
    
    Supports formats:
        https://github.com/owner/repo/pull/123
        owner/repo#123
    """
    # Full URL format
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url
    )
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    # Short format: owner/repo#123
    match = re.match(r"([^/]+)/([^#]+)#(\d+)", url)
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    raise ValueError(
        f"Invalid PR URL: {url}. "
        "Expected: https://github.com/owner/repo/pull/123 or owner/repo#123"
    )


class GitHubClient:
    """Client for GitHub REST API."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.session = requests.Session()
        if self.token:
            self.session.headers["Authorization"] = f"Bearer {self.token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        self.session.headers["User-Agent"] = "claude-review/1.0"

    def fetch_pr(self, owner: str, repo: str, number: int) -> PRData:
        """Fetch PR metadata and diff."""
        # Get PR metadata
        meta_url = f"{self.API_BASE}/repos/{owner}/{repo}/pulls/{number}"
        resp = self.session.get(meta_url)
        resp.raise_for_status()
        meta = resp.json()

        # Get diff
        diff_resp = self.session.get(
            meta_url,
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        diff_resp.raise_for_status()
        diff = diff_resp.text

        return PRData(
            owner=owner,
            repo=repo,
            number=number,
            title=meta["title"],
            body=meta.get("body") or "",
            diff=diff,
            files_changed=meta.get("changed_files", 0),
            additions=meta.get("additions", 0),
            deletions=meta.get("deletions", 0),
            base_branch=meta["base"]["ref"],
            head_branch=meta["head"]["ref"],
            author=meta["user"]["login"],
            url=meta["html_url"],
        )
