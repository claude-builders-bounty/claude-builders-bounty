#!/usr/bin/env python3
"""Produce a deterministic Markdown review for a public GitHub pull request."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    changed_files: int
    additions: int
    deletions: int
    mergeable: bool | None


def parse_pr_url(value: str) -> tuple[str, str, int]:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or parsed.netloc.lower() != "github.com":
        raise ValueError("expected a URL such as https://github.com/owner/repo/pull/123")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 4 or parts[2].lower() != "pull" or not parts[3].isdigit():
        raise ValueError("expected a URL such as https://github.com/owner/repo/pull/123")
    return parts[0], parts[1], int(parts[3])


def github_json(path: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-bounty",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"https://api.github.com{path}", headers=headers, method="GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 403:
            raise RuntimeError("GitHub API rate limit reached; retry later or use GITHUB_TOKEN") from exc
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"could not reach GitHub API: {exc.reason}") from exc


def load_pull_request(url: str) -> tuple[PullRequest, list[dict[str, Any]]]:
    owner, repo, number = parse_pr_url(url)
    base = f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
    metadata = github_json(f"{base}/pulls/{number}")
    files = github_json(f"{base}/pulls/{number}/files?per_page=100")
    if not isinstance(files, list):
        raise RuntimeError("GitHub returned an unexpected files response")
    return (
        PullRequest(
            owner=owner,
            repo=repo,
            number=number,
            title=str(metadata.get("title") or "Untitled pull request"),
            body=str(metadata.get("body") or ""),
            changed_files=int(metadata.get("changed_files") or len(files)),
            additions=int(metadata.get("additions") or 0),
            deletions=int(metadata.get("deletions") or 0),
            mergeable=metadata.get("mergeable") if isinstance(metadata.get("mergeable"), bool) else None,
        ),
        files,
    )


def patch_text(files: list[dict[str, Any]]) -> str:
    chunks: list[str] = []
    for file in files:
        chunks.append(str(file.get("filename") or ""))
        chunks.append(str(file.get("patch") or ""))
    return "\n".join(chunks)


def changed_paths(files: list[dict[str, Any]]) -> list[str]:
    return [str(file.get("filename")) for file in files if file.get("filename")]


def summarize(pr: PullRequest, files: list[dict[str, Any]]) -> list[str]:
    file_word = "file" if pr.changed_files == 1 else "files"
    first = (
        f"This pull request, **#{pr.number} — {pr.title}**, changes "
        f"{pr.changed_files} {file_word} (+{pr.additions}/-{pr.deletions})."
    )
    paths = changed_paths(files)
    if paths:
        preview = ", ".join(f"`{path}`" for path in paths[:4])
        suffix = " and other files" if len(paths) > 4 else ""
        second = f"The visible change surface includes {preview}{suffix}."
    else:
        second = "The GitHub API did not expose individual file patches for this review."
    return [first, second]


def risks(pr: PullRequest, files: list[dict[str, Any]]) -> list[str]:
    text = patch_text(files)
    lower = text.lower()
    paths = changed_paths(files)
    findings: list[str] = []

    if any(re.search(r"(^|/)(\.env|.*secret.*|.*credential.*|.*token.*)$", path, re.I) for path in paths):
        findings.append("**High:** the change touches a file whose name suggests secrets or credentials; verify that no real values are committed.")
    if re.search(r"\b(eval|exec|subprocess|child_process|os\.system)\b", lower):
        findings.append("**High:** dynamic or shell execution appears in the patch; validate inputs and constrain the execution boundary.")
    if re.search(r"(select|insert|update|delete)\s+.*(\+|f['\"]|format\()", lower, re.I):
        findings.append("**High:** SQL assembled through string interpolation appears in the patch; use parameterized queries.")
    if any(path.startswith(".github/workflows/") for path in paths):
        findings.append("**Medium:** CI workflow permissions and untrusted pull-request inputs need an explicit least-privilege review.")
    if any(re.search(r"(^|/)(auth|permissions?|access|middleware)(/|\.|$)", path, re.I) for path in paths):
        findings.append("**Medium:** authorization-sensitive paths changed; add negative tests for unauthorized and cross-tenant access.")
    if any(path in {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.toml", "Cargo.lock", "pyproject.toml", "requirements.txt"} for path in paths):
        findings.append("**Medium:** dependency metadata changed; review provenance, versions, and the resulting lockfile diff.")
    if any(file.get("status") == "removed" and re.search(r"test|spec", str(file.get("filename")), re.I) for file in files):
        findings.append("**Medium:** test files were removed; confirm equivalent coverage exists elsewhere.")
    if pr.additions + pr.deletions > 1000:
        findings.append("**Low:** the patch is large enough that review should be split into smaller, independently testable changes.")

    return findings or ["No high-risk pattern was detected by the deterministic checks; this is not a security guarantee."]


def suggestions(pr: PullRequest, files: list[dict[str, Any]]) -> list[str]:
    paths = changed_paths(files)
    result: list[str] = []
    if not any(re.search(r"(^|/)(test|tests|spec|__tests__)(/|\.|$)", path, re.I) for path in paths):
        result.append("Add or update focused automated tests for the changed behavior, including one failure path.")
    if not any(re.search(r"(^|/)(readme|docs?)(/|\.|$)", path, re.I) for path in paths):
        result.append("Document the public behavior, configuration, and rollback expectations if this changes a user-facing interface.")
    if pr.mergeable is False:
        result.append("Resolve the reported merge conflict before relying on CI results.")
    result.append("Run the repository's formatter, linter, and full test suite before merging.")
    return result


def confidence(pr: PullRequest, files: list[dict[str, Any]]) -> str:
    if not files or any("patch" not in file for file in files):
        return "Low"
    if pr.changed_files <= 20 and pr.additions + pr.deletions <= 1000:
        return "High"
    return "Medium"


def render_review(pr: PullRequest, files: list[dict[str, Any]]) -> str:
    lines = [
        f"# Review: {pr.title}",
        "",
        f"PR: https://github.com/{pr.owner}/{pr.repo}/pull/{pr.number}",
        "",
        "## Summary",
        "",
    ]
    lines.extend(f"{sentence}" for sentence in summarize(pr, files))
    lines.extend(["", "## Identified risks", ""])
    lines.extend(f"- {item}" for item in risks(pr, files))
    lines.extend(["", "## Improvement suggestions", ""])
    lines.extend(f"- {item}" for item in suggestions(pr, files))
    lines.extend(["", "## Confidence", "", confidence(pr, files), ""])
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, help="public GitHub pull-request URL")
    parser.add_argument("--output", help="write Markdown to this path instead of stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        pr, files = load_pull_request(args.pr)
        output = render_review(pr, files) + "\n"
    except (RuntimeError, ValueError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 2
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(output)
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
