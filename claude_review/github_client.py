"""GitHub API client: fetch PR metadata + diff via the REST API."""

from __future__ import annotations

import os
import urllib.request


class GitHubClient:
    """Minimal GitHub REST client (no external deps)."""

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")

    def _opener(self) -> urllib.request.OpenerDirector:
        # trust_env=False: avoid system proxy hijacking local/CI calls
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def _headers(self, accept: str = "application/vnd.github+json") -> dict[str, str]:
        h = {
            "Accept": accept,
            "User-Agent": "claude-review/0.1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    @staticmethod
    def parse_pr_url(url: str) -> tuple[str, str]:
        """Parse https://github.com/owner/repo/pull/N -> (owner/repo, number).

        Handles trailing segments: /pull/123, /pull/123/files, /pull/123/files/1
        """
        parts = [p for p in url.rstrip("/").split("/") if p]
        try:
            idx = parts.index("pull")
        except ValueError as e:
            raise ValueError(f"Not a GitHub PR URL: {url}") from e
        if idx >= 2 and idx + 1 < len(parts) and parts[idx + 1].isdigit():
            return f"{parts[idx-2]}/{parts[idx-1]}", parts[idx + 1]
        raise ValueError(f"Not a GitHub PR URL: {url}")

    def get_pr(self, repo: str, number: str) -> dict:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/pulls/{number}",
            headers=self._headers(),
        )
        with self._opener().open(req, timeout=30) as r:
            return __import__("json").loads(r.read().decode())

    def get_diff(self, repo: str, number: str) -> str:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}/pulls/{number}",
            headers=self._headers(accept="application/vnd.github.v3.diff"),
        )
        with self._opener().open(req, timeout=60) as r:
            return r.read().decode("utf-8", errors="replace")
