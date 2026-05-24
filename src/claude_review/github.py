"""GitHub pull request fetching through gh first, REST second."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
import shutil
import subprocess
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str


@dataclass(frozen=True)
class PullRequestData:
    ref: PullRequestRef
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    state: str
    is_draft: bool
    additions: int
    deletions: int
    changed_files: int
    diff: str
    fetch_source: str


class FetchError(RuntimeError):
    """Raised when PR data cannot be fetched."""


PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)(?:[/?#].*)?$"
)


def parse_pr_url(url: str) -> PullRequestRef:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise ValueError(
            "--pr must be a GitHub pull request URL like "
            "https://github.com/owner/repo/pull/123"
        )
    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
        url=url.strip(),
    )


def fetch_pull_request(ref: PullRequestRef) -> PullRequestData:
    gh_error: Optional[str] = None

    if shutil.which("gh"):
        try:
            return _fetch_with_gh(ref)
        except FetchError as exc:
            gh_error = str(exc)

    try:
        return _fetch_with_rest(ref)
    except FetchError as exc:
        if gh_error:
            raise FetchError(f"gh failed ({gh_error}); REST fallback failed ({exc})")
        raise


def _fetch_with_gh(ref: PullRequestRef) -> PullRequestData:
    metadata_cmd = [
        "gh",
        "pr",
        "view",
        ref.url,
        "--json",
        ",".join(
            [
                "title",
                "body",
                "author",
                "baseRefName",
                "headRefName",
                "additions",
                "deletions",
                "changedFiles",
                "url",
                "state",
                "isDraft",
            ]
        ),
    ]
    diff_cmd = ["gh", "pr", "diff", ref.url, "--color=never"]

    metadata = _run_json(metadata_cmd)
    diff = _run_text(diff_cmd)
    return _metadata_to_pr(ref, metadata, diff, "gh")


def _fetch_with_rest(ref: PullRequestRef) -> PullRequestData:
    api_url = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    metadata = _request_json(api_url, accept="application/vnd.github+json")
    diff = _request_text(api_url, accept="application/vnd.github.diff")
    return _metadata_to_pr(ref, metadata, diff, "github-rest")


def _run_json(cmd: list[str]) -> Dict[str, Any]:
    text = _run_text(cmd)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FetchError(f"{cmd[0]} returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FetchError(f"{cmd[0]} returned unexpected JSON")
    return data


def _run_text(cmd: list[str]) -> str:
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            text=True,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FetchError(str(exc)) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
        raise FetchError(detail)
    return completed.stdout


def _request_json(url: str, accept: str) -> Dict[str, Any]:
    text = _request_text(url, accept=accept)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise FetchError(f"GitHub REST returned invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise FetchError("GitHub REST returned unexpected JSON")
    return data


def _request_text(url: str, accept: str) -> str:
    request = Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": "claude-review/0.1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        message = body.strip() or exc.reason
        raise FetchError(f"GitHub REST HTTP {exc.code}: {message}") from exc
    except URLError as exc:
        raise FetchError(f"GitHub REST request failed: {exc.reason}") from exc


def _metadata_to_pr(
    ref: PullRequestRef, metadata: Dict[str, Any], diff: str, fetch_source: str
) -> PullRequestData:
    author = metadata.get("author")
    if isinstance(author, dict):
        author_name = str(author.get("login") or "unknown")
    else:
        user = metadata.get("user")
        author_name = str(user.get("login") if isinstance(user, dict) else "unknown")

    base = metadata.get("base")
    head = metadata.get("head")
    base_ref = metadata.get("baseRefName") or (
        base.get("ref") if isinstance(base, dict) else ""
    )
    head_ref = metadata.get("headRefName") or (
        head.get("ref") if isinstance(head, dict) else ""
    )

    return PullRequestData(
        ref=ref,
        title=str(metadata.get("title") or ""),
        body=str(metadata.get("body") or ""),
        author=author_name,
        base_ref=str(base_ref or ""),
        head_ref=str(head_ref or ""),
        state=str(metadata.get("state") or "unknown"),
        is_draft=bool(metadata.get("isDraft") or metadata.get("draft")),
        additions=_int(metadata.get("additions")),
        deletions=_int(metadata.get("deletions")),
        changed_files=_int(metadata.get("changedFiles") or metadata.get("changed_files")),
        diff=diff,
        fetch_source=fetch_source,
    )


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
