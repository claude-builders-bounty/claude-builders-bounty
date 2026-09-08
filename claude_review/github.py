"""Standard-library GitHub access. No credentials or environment configuration are used."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlencode

from .core import EmptyDiffError, FileChange, InputValidationError, PullRef, ReviewData, ReviewError

USER_AGENT = "claude-review/1.0.0"
REQUEST_TIMEOUT = 15


class NetworkFailure(ReviewError):
    exit_code = 3


class NotFoundOrPrivate(NetworkFailure):
    pass


class RateLimited(NetworkFailure):
    pass


def _request(url: str, accept: str) -> urllib.request.Request:
    return urllib.request.Request(
        url,
        headers={
            "Accept": accept,
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )


def _read_limited(response: Any, limit: int, label: str) -> bytes:
    raw = response.read(limit + 1)
    if len(raw) > limit:
        raise InputValidationError(f"Oversized {label}: limit is {limit} bytes.")
    return raw


def fetch_bytes(url: str, accept: str, opener: urllib.request.OpenerDirector, limit: int, label: str) -> bytes:
    try:
        with opener.open(_request(url, accept), timeout=REQUEST_TIMEOUT) as response:
            status = getattr(response, "status", 200)
            if status < 200 or status >= 300:
                raise NetworkFailure(f"GitHub request failed with HTTP {status}.")
            return _read_limited(response, limit, label)
    except urllib.error.HTTPError as exc:
        if exc.code in {404, 410}:
            raise NotFoundOrPrivate("Pull request was not found or is private.") from None
        if exc.code == 403:
            remaining = exc.headers.get("X-RateLimit-Remaining")
            if remaining == "0":
                raise RateLimited("GitHub API rate limit was exceeded.") from None
            raise NetworkFailure(f"GitHub request was forbidden with HTTP {exc.code}.") from None
        if exc.code == 422:
            raise NetworkFailure("GitHub rejected the pull-request request.") from None
        raise NetworkFailure(f"GitHub request failed with HTTP {exc.code}.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise NetworkFailure("GitHub network request failed.") from None


def fetch_json(url: str, opener: urllib.request.OpenerDirector, limit: int, label: str) -> Any:
    raw = fetch_bytes(url, "application/vnd.github+json", opener, limit, label)
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise InputValidationError(f"GitHub returned malformed JSON for {label}.") from None


def _file_record(record: Any, index: int) -> dict:
    if not isinstance(record, dict):
        raise InputValidationError(f"GitHub returned a malformed file record at index {index}.")
    return record


def fetch_pull(ref: PullRef, opener: urllib.request.OpenerDirector | None = None) -> ReviewData:
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base_url = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    metadata = fetch_json(base_url, opener, 1_048_576, "metadata.json")
    if not isinstance(metadata, dict):
        raise InputValidationError("GitHub returned malformed pull-request metadata.")
    files_url = base_url + "/files?" + urlencode({"per_page": 100, "page": 1})
    records: list[dict] = []
    for page in range(1, 6):
        page_data = fetch_json(base_url + f"/files?per_page=100&page={page}", opener, 4_194_304, "files.json")
        if not isinstance(page_data, list):
            raise InputValidationError("GitHub returned malformed changed-file records.")
        records.extend(_file_record(item, index) for index, item in enumerate(page_data, len(records)))
        if len(page_data) < 100:
            break
    if len(records) >= 500:
        raise InputValidationError("Oversized pull request: more than 500 changed files are unsupported.")
    diff_url = f"https://github.com/{ref.owner}/{ref.repo}/pull/{ref.number}.diff"
    diff_raw = fetch_bytes(diff_url, "application/vnd.github.v3.diff", opener, 1_048_576, "pr.diff")
    try:
        diff = diff_raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputValidationError("GitHub returned a non-UTF-8 pull-request diff.") from None
    if not diff.strip():
        raise EmptyDiffError("The pull request diff is empty.")

    from .core import parse_diff, parse_files

    files = parse_files(json.dumps(records).encode("utf-8"))
    title = metadata.get("title")
    head = metadata.get("head", {})
    base = metadata.get("base", {})
    head_sha = head.get("sha") if isinstance(head, dict) else None
    base_sha = base.get("sha") if isinstance(base, dict) else None
    metadata_updated_at = metadata.get("updated_at")
    if not isinstance(title, str) or not isinstance(head_sha, str) or not isinstance(base_sha, str):
        raise InputValidationError("GitHub metadata is missing title or head/base SHAs.")
    if not isinstance(metadata_updated_at, str) or not metadata_updated_at:
        raise InputValidationError("GitHub metadata is missing an updated_at timestamp.")
    hunks, merged_files = parse_diff(diff, files)
    return ReviewData(
        ref,
        title,
        head_sha,
        base_sha,
        metadata_updated_at,
        merged_files,
        hunks,
    )


__all__ = ["FileChange", "fetch_pull", "NetworkFailure", "NotFoundOrPrivate", "RateLimited"]
