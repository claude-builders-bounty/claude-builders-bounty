#!/usr/bin/env python3
"""Review a GitHub PR and emit structured Markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

USER_AGENT = "claude-pr-reviewer/1.0"


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    url: str
    changed_files: int
    additions: int
    deletions: int
    diff: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise ValueError(f"Not a GitHub PR URL: {url}")
    owner, repo, number = match.group(1), match.group(2), int(match.group(3))
    return owner, repo.removesuffix(".git"), number


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_text(url: str, accept: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode()


def load_pull_request(pr_url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(pr_url)
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    meta = fetch_json(api)
    diff = fetch_text(f"{api}", "application/vnd.github.v3.diff")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=meta.get("title", ""),
        body=meta.get("body") or "",
        url=meta.get("html_url", pr_url),
        changed_files=meta.get("changed_files", 0),
        additions=meta.get("additions", 0),
        deletions=meta.get("deletions", 0),
        diff=diff,
    )


def summarize(pr: PullRequest) -> str:
    scope = f"{pr.changed_files} files, +{pr.additions}/-{pr.deletions}"
    return (
        f"This PR (**{pr.title}**) updates **{scope}** in `{pr.owner}/{pr.repo}`. "
        f"It appears focused on delivering the described change set for pull request #{pr.number}."
    )


def find_risks(pr: PullRequest) -> list[str]:
    risks: list[str] = []
    diff = pr.diff
    lowered = diff.lower()

    patterns = [
        (r"(?m)^\+.*\b(api[_-]?key|secret|password|token)\s*=", "Possible secret added in diff"),
        (r"(?m)^\+.*\beval\s*\(", "Use of eval() in added code"),
        (r"(?m)^\+.*\bexec\s*\(", "Use of exec() in added code"),
        (r"(?m)^\+.*rm\s+-rf", "Destructive shell command introduced"),
        (r"(?m)^\+.*console\.log\(", "Debug logging left in added code"),
        (r"(?m)^\+.*TODO|FIXME", "Unresolved TODO/FIXME in added lines"),
        (r"(?m)^\+.*@ts-ignore|:\s*any\b", "Type-safety bypass in added TypeScript"),
    ]
    for pattern, message in patterns:
        if re.search(pattern, diff, re.I):
            risks.append(message)

    if pr.additions > 500 and "test" not in lowered:
        risks.append("Large addition without obvious test changes")
    if pr.changed_files > 15:
        risks.append("High file churn — review carefully for unrelated changes")
    if not risks:
        risks.append("No automated high-severity patterns detected")
    return risks


def suggestions(pr: PullRequest) -> list[str]:
    items: list[str] = []
    diff = pr.diff
    if "README" not in diff and pr.changed_files >= 2:
        items.append("Confirm README or usage docs were updated if behavior changed")
    if "test" not in diff.lower() and pr.additions >= 80:
        items.append("Add or extend automated tests for new behavior")
    if pr.body and "Closes #" not in pr.body and "Fixes #" not in pr.body:
        items.append("Link the related issue (`Closes #N`) in the PR description")
    if pr.additions > 0 and pr.deletions == 0 and pr.changed_files == 1:
        items.append("Verify the change is minimal and scoped to one concern")
    if not items:
        items.append("PR looks focused — validate acceptance criteria and run project CI locally")
    return items


def confidence(pr: PullRequest, risks: list[str]) -> str:
    score = 0
    if pr.changed_files <= 5:
        score += 1
    if pr.additions <= 300:
        score += 1
    if len(risks) <= 2 and risks == ["No automated high-severity patterns detected"]:
        score += 2
    elif len(risks) <= 2:
        score += 1
    if "Large addition" in " ".join(risks):
        score -= 1
    if score >= 3:
        return "High"
    if score >= 1:
        return "Medium"
    return "Low"


def render_review(pr: PullRequest) -> str:
    risks = find_risks(pr)
    tips = suggestions(pr)
    level = confidence(pr, risks)
    risk_lines = "\n".join(f"- {item}" for item in risks)
    tip_lines = "\n".join(f"- {item}" for item in tips)
    return f"""## PR Review — #{pr.number}

**PR:** {pr.url}

### Summary

{summarize(pr)}

### Identified risks

{risk_lines}

### Improvement suggestions

{tip_lines}

### Confidence score

**{level}**
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Structured GitHub PR review for Claude Code workflows")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("-o", "--output", help="Write review to file instead of stdout")
    args = parser.parse_args(argv)

    try:
        pr = load_pull_request(args.pr)
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    review = render_review(pr)
    if args.output:
        from pathlib import Path

        Path(args.output).write_text(review, encoding="utf-8")
        print(f"Wrote review to {args.output}")
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
