#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PR_RE = re.compile(r"github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)")
DIFF_FILE_RE = re.compile(r"^diff --git a/(.*?) b/(.*?)$", re.M)


@dataclass
class PullRequest:
    url: str
    owner: str
    repo: str
    number: int
    title: str
    body: str
    additions: int
    deletions: int
    changed_files: int
    files: list[str]
    diff: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_RE.search(url)
    if not match:
        raise ValueError("Expected a GitHub PR URL like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def github_get_json(url: str, token: str | None = None) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed: {exc.code} {detail}") from exc


def github_get_text(url: str, token: str | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub diff request failed: {exc.code} {detail}") from exc


def load_pr(pr_url: str, token: str | None = None) -> PullRequest:
    owner, repo, number = parse_pr_url(pr_url)
    api_base = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    metadata = github_get_json(api_base, token)
    diff = github_get_text(f"https://github.com/{owner}/{repo}/pull/{number}.diff", token)
    files = [match.group(2) for match in DIFF_FILE_RE.finditer(diff)]
    if not files:
        files = []
    return PullRequest(
        url=pr_url,
        owner=owner,
        repo=repo,
        number=number,
        title=metadata.get("title", ""),
        body=metadata.get("body") or "",
        additions=int(metadata.get("additions") or 0),
        deletions=int(metadata.get("deletions") or 0),
        changed_files=int(metadata.get("changed_files") or len(files)),
        files=files,
        diff=diff,
    )


def bullet(items: Iterable[str]) -> str:
    values = [item for item in items if item]
    if not values:
        return "- None identified from the available diff."
    return "\n".join(f"- {item}" for item in values)


def file_groups(files: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {
        "tests": [],
        "docs": [],
        "workflow": [],
        "source": [],
        "generated": [],
    }
    for file in files:
        lower = file.lower()
        if "__pycache__" in lower or lower.endswith((".pyc", ".png", ".jpg", ".jpeg", ".gif")):
            groups["generated"].append(file)
        elif lower.startswith(".github/") or "workflow" in lower:
            groups["workflow"].append(file)
        elif "test" in lower or lower.endswith((".spec.ts", ".test.ts", "_test.py")):
            groups["tests"].append(file)
        elif lower.endswith((".md", ".rst", ".txt")) or "readme" in lower or "docs/" in lower:
            groups["docs"].append(file)
        else:
            groups["source"].append(file)
    return groups


def summarize(pr: PullRequest) -> str:
    groups = file_groups(pr.files)
    touched = []
    for label, files in groups.items():
        if files:
            touched.append(f"{len(files)} {label} file{'s' if len(files) != 1 else ''}")
    touched_text = ", ".join(touched) if touched else "no files detected"
    return (
        f"This PR changes {pr.changed_files} file(s) with {pr.additions} additions and "
        f"{pr.deletions} deletions. It primarily touches {touched_text}. "
        f"The stated goal is: {pr.title}."
    )


def identify_risks(pr: PullRequest) -> list[str]:
    groups = file_groups(pr.files)
    risks: list[str] = []
    diff_lower = pr.diff.lower()

    if pr.additions + pr.deletions > 500:
        risks.append("Large diff size may hide regressions; review by file and run the full relevant test suite.")
    if groups["workflow"]:
        risks.append("Workflow or automation files changed; validate permissions, secrets handling, and trigger scope.")
    if groups["generated"]:
        risks.append("Generated or binary-looking artifacts are present; confirm they are intentional and reproducible.")
    if groups["source"] and not groups["tests"]:
        risks.append("Source files changed without obvious test files in the diff.")
    if re.search(r"(password|secret|token|api[_-]?key)\s*[:=]", diff_lower):
        risks.append("Potential secret-like strings appear in the diff; confirm no real credentials are committed.")
    if "subprocess" in diff_lower or "shell=true" in diff_lower or "os.system" in diff_lower:
        risks.append("Command execution logic appears in the diff; validate argument handling and injection resistance.")
    if "delete" in diff_lower or "drop table" in diff_lower or "truncate" in diff_lower:
        risks.append("Destructive-operation wording appears in the diff; confirm safeguards and tests cover it.")
    return risks


def suggestions(pr: PullRequest) -> list[str]:
    groups = file_groups(pr.files)
    suggestions_list: list[str] = []

    if not groups["tests"]:
        suggestions_list.append("Add or reference tests that exercise the main behavior changed by this PR.")
    if not groups["docs"] and pr.additions > 50:
        suggestions_list.append("Add short usage or maintenance notes for future contributors.")
    if groups["workflow"]:
        suggestions_list.append("Run the workflow in a fork or dry-run mode before merging.")
    if groups["generated"]:
        suggestions_list.append("Document how generated artifacts were produced so maintainers can recreate them.")
    suggestions_list.append("Keep the PR description aligned with the final files and validation commands.")
    return suggestions_list


def confidence(pr: PullRequest, risks: list[str]) -> str:
    groups = file_groups(pr.files)
    if pr.additions + pr.deletions > 800 or len(risks) >= 4:
        return "Low"
    if groups["tests"] and pr.changed_files <= 10 and len(risks) <= 2:
        return "High"
    return "Medium"


def render_review(pr: PullRequest) -> str:
    risks = identify_risks(pr)
    score = confidence(pr, risks)
    changed = "\n".join(f"- `{file}`" for file in pr.files[:20])
    if len(pr.files) > 20:
        changed += f"\n- ...and {len(pr.files) - 20} more file(s)"
    if not changed:
        changed = "- No changed files were parsed from the diff."

    return (
        "## Claude Review\n\n"
        "### Summary\n"
        f"{summarize(pr)}\n\n"
        "### Changed files reviewed\n"
        f"{changed}\n\n"
        "### Identified risks\n"
        f"{bullet(risks)}\n\n"
        "### Improvement suggestions\n"
        f"{bullet(suggestions(pr))}\n\n"
        "### Confidence score\n"
        f"{score}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and print structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--output", help="Write review Markdown to this file")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token, defaults to GITHUB_TOKEN")
    args = parser.parse_args()

    try:
        pr = load_pr(args.pr, args.token)
        review = render_review(pr)
    except Exception as exc:  # noqa: BLE001 - CLI should print actionable errors
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(review, encoding="utf-8")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
