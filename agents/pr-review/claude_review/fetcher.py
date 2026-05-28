"""Fetch PR diff via GitHub API."""

import httpx


class PRFetcher:
    """Fetch pull request data and diff from GitHub."""

    def __init__(self, token: str):
        self.token = token
        self.base = "https://api.github.com"

    def _headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3.diff",
        }

    def fetch_pr(self, url: str) -> dict:
        """Parse and fetch a GitHub PR. Returns {owner, repo, number, title, body, diff, files_changed}."""
        owner, repo, number = self._parse_url(url)
        if not owner:
            raise ValueError(f"Invalid PR URL: {url}")

        api_url = f"{self.base}/repos/{owner}/{repo}/pulls/{number}"

        # Fetch PR metadata (JSON)
        headers_json = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        pr = httpx.get(api_url, headers=headers_json, timeout=30)
        pr.raise_for_status()
        meta = pr.json()

        # Fetch diff (text)
        diff = httpx.get(api_url, headers=self._headers(), timeout=30)
        diff.raise_for_status()
        diff_text = diff.text

        # Count files
        try:
            files = httpx.get(f"{api_url}/files", headers=headers_json, timeout=30)
            files.raise_for_status()
            files_data = files.json()
            files_changed = len(files_data) if isinstance(files_data, list) else 0
        except Exception:
            files_changed = 0

        return {
            "owner": owner,
            "repo": repo,
            "number": number,
            "title": meta.get("title", ""),
            "body": meta.get("body") or "",
            "diff": diff_text[:15000],  # cap for API limits
            "files_changed": files_changed,
            "additions": meta.get("additions", 0),
            "deletions": meta.get("deletions", 0),
            "author": meta.get("user", {}).get("login", ""),
        }

    def _parse_url(self, url: str) -> tuple:
        import re
        m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
        if m:
            return m.group(1), m.group(2), int(m.group(3))
        return None, None, None
