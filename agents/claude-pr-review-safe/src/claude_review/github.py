"""Fetch bounded diffs from public GitHub pull requests."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlsplit


class GitHubError(ValueError):
    """A safe, user-facing error while reading GitHub."""


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repository: str
    number: int

    @property
    def api_path(self) -> str:
        return f"repos/{self.owner}/{self.repository}/pulls/{self.number}"

    @property
    def canonical_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repository}/pull/{self.number}"


_URL_PATH = re.compile(
    r"/([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)/"
    r"([A-Za-z0-9._-]+)/pull/([1-9][0-9]*)/?"
)


def parse_pull_request_url(value: str) -> PullRequest:
    """Accept only a canonical public github.com pull-request URL."""
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError as exc:
        raise GitHubError("Invalid pull request URL.") from exc

    if (
        parts.scheme != "https"
        or parts.hostname != "github.com"
        or parts.username is not None
        or parts.password is not None
        or port is not None
        or parts.query
        or parts.fragment
    ):
        raise GitHubError("Use a public HTTPS github.com pull request URL.")

    match = _URL_PATH.fullmatch(parts.path)
    if not match:
        raise GitHubError("Expected https://github.com/owner/repo/pull/123.")

    owner, repository, number = match.groups()
    if repository in {".", ".."}:
        raise GitHubError("Invalid repository name in pull request URL.")
    return PullRequest(owner, repository, int(number))


def fetch_pull_request_diff(
    pull_request: PullRequest,
    *,
    max_bytes: int = 256_000,
    timeout_seconds: float = 20.0,
) -> str:
    """Fetch a public PR diff without credentials and reject oversized diffs."""
    if max_bytes <= 0:
        raise GitHubError("The maximum diff size must be greater than zero.")

    request = urllib.request.Request(
        f"https://api.github.com/{pull_request.api_path}",
        headers={
            "Accept": "application/vnd.github.diff",
            "User-Agent": "claude-pr-review-safe/0.1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    declared_length = int(content_length)
                except ValueError as exc:
                    raise GitHubError("GitHub returned an invalid diff size.") from exc
                if declared_length > max_bytes:
                    raise GitHubError(
                        f"Pull request diff exceeds the {max_bytes:,}-byte limit. "
                        "Review a smaller PR or raise --max-diff-bytes."
                    )
            payload = response.read(max_bytes + 1)
    except GitHubError:
        raise
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise GitHubError("Pull request was not found or is not public.") from exc
        if exc.code == 403:
            raise GitHubError(
                "GitHub refused the request; the public API rate limit may be exhausted."
            ) from exc
        raise GitHubError(
            f"GitHub returned HTTP {exc.code} while fetching the diff."
        ) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise GitHubError("Could not reach the GitHub API.") from exc

    if len(payload) > max_bytes:
        raise GitHubError(
            f"Pull request diff exceeds the {max_bytes:,}-byte limit. "
            "Review a smaller PR or raise --max-diff-bytes."
        )

    try:
        diff = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GitHubError("GitHub returned a diff that is not valid UTF-8.") from exc
    if not diff.strip():
        raise GitHubError("The pull request has an empty diff.")
    return diff
