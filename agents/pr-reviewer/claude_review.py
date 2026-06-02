#!/usr/bin/env python3
"""Generate a structured Markdown PR review from a GitHub pull request diff."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


if sys.version_info < (3, 8):
    raise SystemExit("claude_review.py requires Python 3.8 or newer.")


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$")
RISKY_PATTERNS = (
    ("SQL data destruction handling", re.compile(r"(?i)\b(drop\s+table|truncate\s+(?:table\s+)?\w+|delete\s+from)\b")),
    ("authentication or authorization changes", re.compile(r"(?i)\b(auth|session|permission|role|jwt|oauth)\b")),
    ("billing or payment changes", re.compile(r"(?i)\b(billing|stripe|invoice|payment|checkout)\b")),
    ("destructive shell or git operations", re.compile(r"(?i)\b(rm\s+(?=[^;&|\n]*(?:-[A-Za-z]*r|--recursive))(?=[^;&|\n]*(?:-[A-Za-z]*f|--force))[^;&|\n]*|git\s+push\b[^\n;&|]*(?:--force|-f\b))")),
    ("secret or environment handling", re.compile(r"(?i)\b(secret|api[_-]?key|process\.env|env\.)\b|\.env\b")),
)
TEST_PATH_RE = re.compile(
    r"(?i)(^|/)(__tests__|tests?|test_[^/]*|[^/]*_(?:test|spec)\.[^/]+|[^/]*\.(?:test|spec)\.[^/]+)(/|$)"
)
DIFF_HEADER_PREFIX = "diff --git "
DIFF_HEADER_SEPARATOR = " b/"


@dataclass(frozen=True)
class ChangedFile:
    path: str
    added: int
    deleted: int


@dataclass(frozen=True)
class PullRequestDiff:
    owner: str
    repo: str
    number: str
    title: str
    files: Tuple[ChangedFile, ...]
    added_lines: Tuple[str, ...]
    raw_diff: str


def parse_pr_url(url: str) -> Tuple[str, str, str]:
    match = PR_RE.match(url)
    if not match:
        raise SystemExit(
            "Expected a GitHub PR URL like https://github.com/owner/repo/pull/123; "
            f"got {short_text(url)!r}"
        )
    return match.group(1), match.group(2), match.group(3)


def github_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_diff(owner: str, repo: str, number: str) -> str:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    request = urllib.request.Request(url, headers=github_headers())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8", errors="replace")
            return validate_diff_response(text)
    except urllib.error.HTTPError as exc:
        raise SystemExit(format_http_error(exc, url)) from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub request failed: {exc.reason}") from exc


def short_text(value: str, limit: int = 120) -> str:
    compact = value.replace("\r", "\\r").replace("\n", "\\n")
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def github_json_message(text: str) -> Optional[str]:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
        return payload["message"]
    return None


def format_http_error(exc: urllib.error.HTTPError, url: str) -> str:
    try:
        body = exc.read().decode("utf-8", errors="replace")
    except Exception:
        body = ""
    message = github_json_message(body.lstrip()) if body else None
    if message:
        detail = f": {message.rstrip('.')}"
    elif body.lstrip().startswith("{"):
        detail = ": JSON error payload did not include a message field; check authentication, PR visibility, or rate limits"
    else:
        detail = ""
    return f"GitHub request failed with HTTP {exc.code}{detail}. URL: {url}"


def validate_diff_response(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("<"):
        raise SystemExit("GitHub returned HTML instead of a diff; check authentication or PR visibility.")
    if stripped.startswith("{"):
        message = github_json_message(stripped)
        if message:
            detail = f": {message.rstrip('.')}"
        else:
            detail = ": JSON payload did not include a message field; check authentication, PR visibility, or rate limits"
        raise SystemExit(f"GitHub returned JSON instead of a diff{detail}.")
    if not stripped.startswith("diff --git "):
        raise SystemExit("GitHub response did not look like a PR diff; check the PR URL, authentication, or rate limits.")
    return text


def path_from_diff_header(line: str) -> Optional[str]:
    if not line.startswith(DIFF_HEADER_PREFIX):
        return None
    rest = line[len(DIFF_HEADER_PREFIX):]
    if rest.startswith(("'", '"')):
        try:
            parts = shlex.split(rest)
        except ValueError:
            return None
        if len(parts) >= 2 and parts[1].startswith("b/"):
            return parts[1][2:]
        return None
    if not rest.startswith("a/") or DIFF_HEADER_SEPARATOR not in rest:
        return None
    return rest[len("a/"):].split(DIFF_HEADER_SEPARATOR, 1)[1]


def parse_diff(owner: str, repo: str, number: str, raw_diff: str) -> PullRequestDiff:
    title = f"{owner}/{repo}#{number}"
    files: List[ChangedFile] = []
    current_path: Optional[str] = None
    fallback_path: Optional[str] = None
    added = 0
    deleted = 0
    in_hunk = False
    added_lines: List[str] = []

    def finish_file() -> None:
        nonlocal current_path, fallback_path, added, deleted, in_hunk
        path = current_path or fallback_path
        if path is not None:
            files.append(ChangedFile(path, added, deleted))
        current_path = None
        fallback_path = None
        added = 0
        deleted = 0
        in_hunk = False

    for line in raw_diff.splitlines():
        if line.startswith(DIFF_HEADER_PREFIX):
            finish_file()
            fallback_path = path_from_diff_header(line)
            continue
        if line.startswith("@@ "):
            in_hunk = True
            continue
        if in_hunk:
            if line.startswith("\\"):
                continue
            if line.startswith("+"):
                added += 1
                added_lines.append(line[1:])
            elif line.startswith("-"):
                deleted += 1
            continue
        if line.startswith("+++ "):
            marker = line[4:]
            if marker == "/dev/null":
                current_path = fallback_path
            elif marker.startswith("b/"):
                current_path = marker[2:]
            continue
        if line.startswith("--- "):
            continue

    finish_file()

    return PullRequestDiff(owner, repo, number, title, tuple(files), tuple(added_lines), raw_diff)


def summarize_files(files: Iterable[ChangedFile]) -> str:
    file_list = list(files)
    if not file_list:
        return "No changed files were found in the diff."
    total_added = sum(file.added for file in file_list)
    total_deleted = sum(file.deleted for file in file_list)
    top_files = sorted(file_list, key=lambda file: file.added + file.deleted, reverse=True)[:3]
    names = ", ".join(file.path for file in top_files)
    return f"The diff changes {len(file_list)} file(s), with {total_added} added and {total_deleted} deleted line(s). The largest changes are in {names}."


def detect_risks(pr: PullRequestDiff) -> List[str]:
    haystack = review_haystack(pr)
    risks: List[str] = []
    for label, pattern in RISKY_PATTERNS:
        if pattern.search(haystack):
            risks.append(f"- Review {label}; the diff contains related paths or commands.")

    if not has_test_file(pr):
        risks.append("- No test file change is visible, so behavior may rely on manual verification.")

    large_files = [file for file in pr.files if file.added + file.deleted > 250]
    if large_files:
        names = ", ".join(file.path for file in large_files[:3])
        risks.append(f"- Large changes in {names} may hide multiple concerns in one review.")

    return risks or ["- No major risks found in the reviewed diff."]


def suggestions(pr: PullRequestDiff) -> List[str]:
    haystack = review_haystack(pr)
    items: List[str] = []
    if not has_test_file(pr):
        items.append("- Add a small focused test or sample output that exercises the main changed behavior.")
    if re.search(r"(?i)(cli|argparse|command)", haystack):
        items.append("- Document the exact CLI invocation and at least one expected output snippet.")
    if re.search(r"(?i)(drop\s+table|truncate|delete\s+from|sql)", haystack):
        items.append("- Add cases for quoted SQL, semicolon-separated SQL, and safe DELETE statements with WHERE clauses.")
    if re.search(r"(?i)(hook|bash|shell)", haystack):
        items.append("- Include one allowed and one denied shell example so reviewers can reproduce the boundary.")
    if not items:
        items.append("- Keep the PR scoped to the current behavior and add a regression example if a bug motivated it.")
    return items


def review_haystack(pr: PullRequestDiff) -> str:
    paths = "\n".join(file.path for file in pr.files)
    additions = "\n".join(pr.added_lines)
    return f"{paths}\n{additions}"


def has_test_file(pr: PullRequestDiff) -> bool:
    return any(TEST_PATH_RE.search(file.path) for file in pr.files)


def confidence(pr: PullRequestDiff) -> str:
    if not pr.files:
        return "Low - The diff did not expose changed files."
    total_lines = sum(file.added + file.deleted for file in pr.files)
    if total_lines > 600:
        return "Medium - The diff is reviewable, but the change size limits confidence without running project tests."
    return "High - The diff is small enough for a reliable static review, assuming the fetched PR diff is complete."


def render_review(pr: PullRequestDiff, pr_url: str) -> str:
    summary = summarize_files(pr.files)
    risks = "\n".join(detect_risks(pr))
    improvements = "\n".join(suggestions(pr))
    return (
        "## Summary\n"
        f"This review covers [{pr.title}]({pr_url}). {summary} "
        "The review is based on the GitHub diff and focuses on implementation risk, test coverage, and maintainability.\n\n"
        "## Identified Risks\n"
        f"{risks}\n\n"
        "## Improvement Suggestions\n"
        f"{improvements}\n\n"
        "## Confidence\n"
        f"{confidence(pr)}\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL.")
    parser.add_argument("-o", "--output", help="Optional file path for the Markdown review.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    owner, repo, number = parse_pr_url(args.pr)
    raw_diff = fetch_diff(owner, repo, number)
    pr = parse_diff(owner, repo, number, raw_diff)
    review_text = render_review(pr, args.pr)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(review_text, encoding="utf-8")
    else:
        print(review_text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
