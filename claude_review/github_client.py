"""GitHub API client for fetching pull request metadata and diffs."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Optional

PR_URL_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)$"
)


class GitHubError(Exception):
    """Raised when the GitHub API returns an error."""


@dataclass
class PullRequest:
    """Normalized pull request data."""

    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    diff: str
    changed_files: list = field(default_factory=list)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a PR URL into (owner, repo, number)."""
    m = PR_URL_RE.match(url.strip())
    if not m:
        raise ValueError(
            f"Invalid PR URL: {url!r}. Expected https://github.com/owner/repo/pull/123"
        )
    return m.group("owner"), m.group("repo"), int(m.group("number"))


def _api_request(url: str, token: Optional[str] = None) -> dict:
    """Perform an authenticated GET request against the GitHub API."""
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise GitHubError(f"GitHub API error {e.code} for {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise GitHubError(f"Network error for {url}: {e.reason}") from e


def _diff_request(url: str, token: Optional[str] = None) -> str:
    """Fetch a raw diff (Accept: application/vnd.github.v3.diff)."""
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        raise GitHubError(f"GitHub API error {e.code} for {url}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise GitHubError(f"Network error for {url}: {e.reason}") from e


def get_token() -> Optional[str]:
    """Return a GitHub token from the environment, if present."""
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def fetch_pull_request(url: str, token: Optional[str] = None) -> PullRequest:
    """Fetch PR metadata + diff from the GitHub API."""
    owner, repo, number = parse_pr_url(url)
    token = token or get_token()

    meta = _api_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", token
    )
    diff = _diff_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", token
    )

    files = _api_request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100",
        token,
    )

    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=meta.get("title", ""),
        body=meta.get("body") or "",
        author=(meta.get("user") or {}).get("login", "unknown"),
        base_ref=(meta.get("base") or {}).get("ref", ""),
        head_ref=(meta.get("head") or {}).get("ref", ""),
        diff=diff,
        changed_files=[
            {
                "filename": f.get("filename", ""),
                "status": f.get("status", ""),
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "patch": f.get("patch", ""),
            }
            for f in files
        ],
    )