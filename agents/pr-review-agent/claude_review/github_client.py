"""GitHub API client for fetching PR data and diffs."""

import re
import sys
import requests
from dataclasses import dataclass
from typing import Optional


@dataclass
class PRInfo:
    """Structured pull request information."""
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base_branch: str
    head_branch: str
    state: str
    additions: int
    deletions: int
    changed_files: int
    diff: str
    url: str
    files: list


def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse a GitHub PR URL into (owner, repo, pull_number).

    Supports formats:
      - https://github.com/owner/repo/pull/123
      - https://github.com/owner/repo/pull/new/branch-name (treat as branch ref)
      - owner/repo#123
    """
    # Standard PR URL
    match = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)",
        url.strip().rstrip("/"),
    )
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    # Shorthand: owner/repo#123
    match = re.match(r"([^/]+)/([^/#]+)#(\d+)", url.strip())
    if match:
        return match.group(1), match.group(2), int(match.group(3))

    raise ValueError(
        f"Cannot parse PR URL: {url}\n"
        "Expected format: https://github.com/owner/repo/pull/123 or owner/repo#123"
    )


class GitHubClient:
    """Client to interact with GitHub API for PR data."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "claude-pr-review-agent/1.0",
        })
        if token:
            self.session.headers["Authorization"] = f"token {token}"

    def get_pr_info(self, owner: str, repo: str, number: int) -> PRInfo:
        """Fetch full PR information including diff."""
        # Get PR metadata
        pr_url = f"{self.API_BASE}/repos/{owner}/{repo}/pulls/{number}"
        resp = self.session.get(pr_url)
        if resp.status_code == 404:
            raise ValueError(f"PR not found: {owner}/{repo}#{number}")
        resp.raise_for_status()
        pr_data = resp.json()

        # Get PR diff
        diff_resp = self.session.get(
            pr_url,
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        diff_resp.raise_for_status()
        diff_text = diff_resp.text

        # Get file list
        files_resp = self.session.get(f"{pr_url}/files", params={"per_page": 100})
        files_resp.raise_for_status()
        files_data = files_resp.json()

        file_list = []
        for f in files_data:
            file_list.append({
                "filename": f.get("filename", ""),
                "status": f.get("status", ""),
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "changes": f.get("changes", 0),
                "patch": f.get("patch", ""),
            })

        return PRInfo(
            owner=owner,
            repo=repo,
            number=number,
            title=pr_data.get("title", ""),
            body=pr_data.get("body", "") or "",
            author=pr_data.get("user", {}).get("login", "unknown"),
            base_branch=pr_data.get("base", {}).get("ref", ""),
            head_branch=pr_data.get("head", {}).get("ref", ""),
            state=pr_data.get("state", ""),
            additions=pr_data.get("additions", 0),
            deletions=pr_data.get("deletions", 0),
            changed_files=pr_data.get("changed_files", 0),
            diff=diff_text,
            url=pr_data.get("html_url", ""),
            files=file_list,
        )

    def post_review_comment(self, owner: str, repo: str, number: int, body: str):
        """Post a review comment on a PR (requires auth token)."""
        url = f"{self.API_BASE}/repos/{owner}/{repo}/issues/{number}/comments"
        resp = self.session.post(url, json={"body": body})
        resp.raise_for_status()
        return resp.json()
