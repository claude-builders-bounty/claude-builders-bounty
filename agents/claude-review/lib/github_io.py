"""GitHub PR fetch helpers for claude-review."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

PR_URL_RE = re.compile(
    r"https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)",
    re.I,
)
PR_SHORT_RE = re.compile(r"^(?P<owner>[^/]+)/(?P<repo>[^/]+)#(?P<number>\d+)$")


@dataclass
class FileChange:
    path: str
    status: str
    additions: int
    deletions: int
    patch: str = ""


@dataclass
class Review:
    title: str
    url: str
    summary: str
    risks: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: str = "Medium"
    files: List[FileChange] = field(default_factory=list)
    mode: str = "heuristic"


def parse_pr_ref(ref: str) -> Tuple[str, str, int]:
    ref = ref.strip()
    m = PR_URL_RE.match(ref) or PR_SHORT_RE.match(ref)
    if not m:
        raise SystemExit(
            f"Invalid --pr value: {ref!r}\n"
            "Expected https://github.com/owner/repo/pull/N or owner/repo#N"
        )
    return m.group("owner"), m.group("repo"), int(m.group("number"))


def gh_get(path: str, accept: str = "application/vnd.github+json") -> Any:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "claude-review/1.0"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if "json" in accept:
                return json.loads(raw.decode("utf-8"))
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API {e.code} for {path}: {body[:300]}") from e


def fetch_pr(owner: str, repo: str, number: int) -> Tuple[dict, List[FileChange]]:
    meta = gh_get(f"/repos/{owner}/{repo}/pulls/{number}")
    files_raw = gh_get(f"/repos/{owner}/{repo}/pulls/{number}/files?per_page=100")
    files = [
        FileChange(
            path=f.get("filename", ""),
            status=f.get("status", ""),
            additions=int(f.get("additions") or 0),
            deletions=int(f.get("deletions") or 0),
            patch=f.get("patch") or "",
        )
        for f in files_raw
    ]
    return meta, files
