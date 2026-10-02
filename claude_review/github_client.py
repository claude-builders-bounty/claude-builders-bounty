"""GitHub API client for fetching PR diffs and metadata."""

import re
import requests

GITHUB_API = "https://api.github.com"

def parse_pr_url(url):
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError(f"Cannot parse PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))

def get_pr_diff(owner, repo, pr_number, token=None):
    headers = {"Accept": "application/vnd.github.v3.diff"}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 404:
        raise RuntimeError(f"PR not found: {owner}/{repo}#{pr_number}")
    resp.raise_for_status()
    return resp.text

def get_pr_meta(owner, repo, pr_number, token=None):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}"
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    d = resp.json()
    return {
        "title": d.get("title", ""),
        "author": d.get("user", {}).get("login", "unknown"),
        "body": d.get("body", "") or "",
        "html_url": d.get("html_url", ""),
        "state": d.get("state", ""),
        "additions": d.get("additions", 0),
        "deletions": d.get("deletions", 0),
        "changed_files": d.get("changed_files", 0),
    }
