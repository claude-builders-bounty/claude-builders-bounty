#!/usr/bin/env python3
"""Generate a structured Markdown PR review from a GitHub pull request diff."""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    removed: int
    patch: str


def request_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review",
    }
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API request failed: {exc.code} {body}") from exc


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.fullmatch(url.strip())
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def fetch_pr(owner: str, repo: str, number: str) -> tuple[dict, list[FileChange]]:
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    pr = request_json(api)
    files: list[FileChange] = []
    page = 1
    while True:
        batch = request_json(f"{api}/files?per_page=100&page={page}")
        if not batch:
            break
        for item in batch:
            files.append(
                FileChange(
                    path=item["filename"],
                    added=int(item.get("additions", 0)),
                    removed=int(item.get("deletions", 0)),
                    patch=item.get("patch", ""),
                )
            )
        page += 1
    return pr, files


def risk_signals(files: Iterable[FileChange]) -> list[str]:
    signals: list[str] = []
    for file in files:
        lower = file.path.lower()
        patch = file.patch.lower()
        if any(part in lower for part in ("auth", "login", "token", "secret", "permission")):
            signals.append(f"`{file.path}` touches authentication, authorization, or secret-handling code.")
        if any(part in lower for part in ("migration", "schema", "database", "sql")):
            signals.append(f"`{file.path}` changes persistence/database behavior; verify migration and rollback paths.")
        if "delete from" in patch and "where" not in patch:
            signals.append(f"`{file.path}` includes a `DELETE FROM` statement that may need a scoped `WHERE` clause.")
        if "fetch(" in patch or "http" in patch:
            signals.append(f"`{file.path}` touches network calls; check timeout, retry, and error handling behavior.")
        if file.added + file.removed > 400:
            signals.append(f"`{file.path}` is a large change ({file.added + file.removed} lines), raising review risk.")
    return dedupe(signals)[:8]


def suggestions(files: list[FileChange]) -> list[str]:
    result = [
        "Run the narrowest test command that exercises the changed paths and paste the output into the PR.",
        "Document any manual verification steps that reviewers cannot reproduce from CI alone.",
    ]
    if any("test" not in file.path.lower() for file in files) and not any("test" in file.path.lower() for file in files):
        result.append("Add at least one regression test or fixture that proves the new behavior.")
    if any(file.path.lower().endswith((".md", ".mdx")) for file in files):
        result.append("Preview rendered documentation to catch broken links, heading hierarchy issues, and stale examples.")
    if any(file.path.lower().endswith((".yml", ".yaml")) for file in files):
        result.append("Validate workflow/config YAML with the target tool before merge.")
    return dedupe(result)[:6]


def dedupe(items: Iterable[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def confidence(files: list[FileChange], risks: list[str]) -> str:
    total = sum(file.added + file.removed for file in files)
    if total > 800 or len(risks) >= 5:
        return "Low"
    if total > 250 or len(risks) >= 2:
        return "Medium"
    return "High"


def render_review(pr: dict, files: list[FileChange]) -> str:
    changed = len(files)
    additions = sum(file.added for file in files)
    deletions = sum(file.removed for file in files)
    risks = risk_signals(files)
    tips = suggestions(files)
    title = pr.get("title", "Untitled PR")
    summary = (
        f"This PR, **{title}**, changes {changed} file(s) with {additions} additions "
        f"and {deletions} deletions. The main review focus should be the changed file set, "
        "risk-bearing paths, and whether the submitted verification covers the behavior."
    )

    lines = [
        "## Summary",
        "",
        summary,
        "",
        "## Identified Risks",
        "",
    ]
    lines.extend(f"- {risk}" for risk in (risks or ["No high-risk patterns were detected from filenames or patch text."]))
    lines.extend(["", "## Improvement Suggestions", ""])
    lines.extend(f"- {tip}" for tip in tips)
    lines.extend(["", "## Confidence", "", confidence(files, risks)])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and print structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL.")
    parser.add_argument("--output", help="Optional file to write the Markdown review.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    owner, repo, number = parse_pr_url(args.pr)
    pr, files = fetch_pr(owner, repo, number)
    review = render_review(pr, files)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(review)
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
