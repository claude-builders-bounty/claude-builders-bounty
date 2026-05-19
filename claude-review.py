#!/usr/bin/env python3
"""Generate a structured Markdown review for a GitHub pull request."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)/?$")


@dataclass
class FileChange:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str


def github_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-review-agent",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub request failed: HTTP {exc.code} {message}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"GitHub request failed: {exc.reason}") from exc


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.match(url)
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def fetch_pull_request(pr_url: str) -> tuple[dict, list[FileChange]]:
    owner, repo, number = parse_pr_url(pr_url)
    pr_data = github_json(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
    files_data = github_json(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100")
    if not isinstance(pr_data, dict) or not isinstance(files_data, list):
        raise SystemExit("Unexpected GitHub API response shape")

    files = [
        FileChange(
            filename=str(item.get("filename", "")),
            status=str(item.get("status", "")),
            additions=int(item.get("additions", 0) or 0),
            deletions=int(item.get("deletions", 0) or 0),
            patch=str(item.get("patch", "") or ""),
        )
        for item in files_data
    ]
    return pr_data, files


def bucket_files(files: Iterable[FileChange]) -> dict[str, int]:
    buckets = {
        "tests": 0,
        "docs": 0,
        "ci": 0,
        "source": 0,
        "config": 0,
    }
    for file in files:
        name = file.filename.lower()
        if name.startswith("test") or "/test" in name or name.endswith((".spec.ts", ".test.ts", ".test.py")):
            buckets["tests"] += 1
        elif name.endswith((".md", ".rst", ".txt")) or name.startswith("docs/"):
            buckets["docs"] += 1
        elif name.startswith(".github/") or "workflow" in name:
            buckets["ci"] += 1
        elif name.endswith((".json", ".yml", ".yaml", ".toml", ".ini")):
            buckets["config"] += 1
        else:
            buckets["source"] += 1
    return buckets


def detect_risks(files: list[FileChange]) -> list[str]:
    risks: list[str] = []
    total_delta = sum(file.additions + file.deletions for file in files)
    test_files = [file for file in files if "test" in file.filename.lower()]
    source_files = [
        file
        for file in files
        if file.filename not in {test.filename for test in test_files}
        and not file.filename.lower().endswith((".md", ".rst", ".txt", ".json", ".yml", ".yaml", ".toml", ".ini"))
        and not file.filename.lower().startswith(("docs/", ".github/"))
    ]

    if total_delta > 500:
        risks.append("Large diff size increases review risk; consider splitting unrelated changes.")
    if source_files and not test_files:
        risks.append("Source files changed without matching test changes.")
    for file in files:
        patch = file.patch.lower()
        if "delete from" in patch and "where" not in patch:
            risks.append(f"{file.filename}: SQL deletion appears without an obvious WHERE guard.")
        if "subprocess" in patch or "shell=true" in patch:
            risks.append(f"{file.filename}: subprocess usage needs input validation and error handling review.")
        if "token" in patch or "secret" in patch or "api_key" in patch:
            risks.append(f"{file.filename}: credential-related text changed; verify no secrets are committed.")
        if file.status == "removed":
            risks.append(f"{file.filename}: removed file may affect downstream users or documentation links.")
    return risks or ["No major structural risks detected from the public diff metadata."]


def suggestions(files: list[FileChange], risks: list[str]) -> list[str]:
    output = []
    if any("without matching test" in risk for risk in risks):
        output.append("Add focused regression tests or document why the change is docs/config-only.")
    if len(files) > 10:
        output.append("Group the PR description by subsystem so reviewers can follow the change surface.")
    if any(file.filename.endswith(".md") for file in files):
        output.append("Check Markdown links and command snippets after the final rebase.")
    if any(file.filename.startswith(".github/") for file in files):
        output.append("Run the affected workflow or a local equivalent before merge.")
    output.append("Keep the PR body updated with exact verification commands and results.")
    return output


def confidence(files: list[FileChange], risks: list[str]) -> str:
    total_delta = sum(file.additions + file.deletions for file in files)
    serious = [risk for risk in risks if "SQL" in risk or "credential" in risk or "subprocess" in risk]
    if serious or total_delta > 800:
        return "Low"
    if total_delta > 250 or any("without matching test" in risk for risk in risks):
        return "Medium"
    return "High"


def render_review(pr: dict, files: list[FileChange]) -> str:
    title = str(pr.get("title", "Untitled PR"))
    url = str(pr.get("html_url", ""))
    total_additions = sum(file.additions for file in files)
    total_deletions = sum(file.deletions for file in files)
    buckets = bucket_files(files)
    risks = detect_risks(files)
    review_suggestions = suggestions(files, risks)
    confidence_score = confidence(files, risks)

    touched = ", ".join(f"{name}: {count}" for name, count in buckets.items() if count)
    if not touched:
        touched = "no files reported"

    lines = [
        "## Claude Review",
        "",
        "### Summary",
        f"This PR, `{title}`, changes {len(files)} file(s) with +{total_additions}/-{total_deletions} lines.",
        f"The touched areas are: {touched}.",
        f"PR: {url}",
        "",
        "### Identified Risks",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.extend(["", "### Improvement Suggestions"])
    lines.extend(f"- {item}" for item in review_suggestions)
    lines.extend(["", f"### Confidence Score: {confidence_score}"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown PR review.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    args = parser.parse_args()

    pr, files = fetch_pull_request(args.pr)
    print(render_review(pr, files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
