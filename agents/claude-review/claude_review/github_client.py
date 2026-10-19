"""
GitHub API and Diff Client for Claude Review Agent
"""
import os
import re
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple, Optional

PR_URL_REGEX = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?"
)

class GitHubClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or ""
        self.headers = {
            "User-Agent": "claude-review-agent/1.0",
            "Accept": "application/vnd.github.v3+json"
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    @staticmethod
    def parse_pr_url(url: str) -> Tuple[str, str, int]:
        m = PR_URL_REGEX.match(url.strip())
        if not m:
            # Check shorthand format: owner/repo#123 or owner/repo/pull/123
            shorthand = re.match(r"(?P<owner>[^/]+)/(?P<repo>[^/#]+)(?:/pull/|#)(?P<number>\d+)", url.strip())
            if shorthand:
                return shorthand.group("owner"), shorthand.group("repo"), int(shorthand.group("number"))
            raise ValueError(f"Invalid GitHub PR URL or reference: {url}. Expected format: https://github.com/owner/repo/pull/123")
        return m.group("owner"), m.group("repo"), int(m.group("number"))

    def get_pr_metadata(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        req = urllib.request.Request(api_url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "owner": owner,
                    "repo": repo,
                    "number": pr_number,
                    "title": data.get("title", ""),
                    "author": data.get("user", {}).get("login", "unknown"),
                    "state": data.get("state", "open"),
                    "base_branch": data.get("base", {}).get("ref", "main"),
                    "head_branch": data.get("head", {}).get("ref", ""),
                    "body": data.get("body", "") or "",
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "changed_files": data.get("changed_files", 0),
                    "html_url": data.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pr_number}")
                }
        except urllib.error.HTTPError as e:
            if e.code == 404 and not self.token:
                # Private or rate-limited without token
                return {
                    "owner": owner,
                    "repo": repo,
                    "number": pr_number,
                    "title": f"PR #{pr_number}",
                    "author": "contributor",
                    "state": "open",
                    "base_branch": "main",
                    "head_branch": "branch",
                    "body": "",
                    "additions": 0,
                    "deletions": 0,
                    "changed_files": 0,
                    "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}"
                }
            raise RuntimeError(f"GitHub API error ({e.code}) while fetching PR #{pr_number}: {e.reason}")

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        # First attempt: Official GitHub REST API with diff media type
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        diff_headers = dict(self.headers)
        diff_headers["Accept"] = "application/vnd.github.v3.diff"
        
        req = urllib.request.Request(api_url, headers=diff_headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception:
            # Fallback attempt: Public web .diff URL
            web_diff_url = f"https://github.com/{owner}/{repo}/pull/{pr_number}.diff"
            fallback_req = urllib.request.Request(web_diff_url, headers={"User-Agent": "claude-review-agent/1.0"})
            with urllib.request.urlopen(fallback_req, timeout=20) as resp:
                return resp.read().decode("utf-8", errors="replace")

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, comment_markdown: str) -> str:
        if not self.token:
            raise ValueError("Cannot post PR comment: GITHUB_TOKEN is required. Set GITHUB_TOKEN environment variable or pass --github-token.")
        
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        payload = json.dumps({"body": comment_markdown}).encode("utf-8")
        headers = dict(self.headers)
        headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("html_url", "")
