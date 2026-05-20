from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


PR_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)")


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base: str
    head: str
    changed_files: int
    additions: int
    deletions: int
    diff: str


def _headers(accept: str = "application/vnd.github+json") -> dict[str, str]:
    h = {"Accept": accept, "User-Agent": "claude-pr-review-agent"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def _get_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_text(url: str, accept: str) -> str:
    req = urllib.request.Request(url, headers=_headers(accept))
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_RE.fullmatch(url.strip())
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr(pr_url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(pr_url)
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    meta = _get_json(api)
    diff = _get_text(api, "application/vnd.github.v3.diff")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=meta.get("title") or "",
        body=meta.get("body") or "",
        author=(meta.get("user") or {}).get("login") or "unknown",
        base=(meta.get("base") or {}).get("ref") or "unknown",
        head=(meta.get("head") or {}).get("ref") or "unknown",
        changed_files=int(meta.get("changed_files") or 0),
        additions=int(meta.get("additions") or 0),
        deletions=int(meta.get("deletions") or 0),
        diff=diff,
    )


def _changed_paths(diff: str) -> list[str]:
    paths = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                paths.append(parts[3][2:] if parts[3].startswith("b/") else parts[3])
    return paths


def heuristic_review(pr: PullRequest) -> str:
    paths = _changed_paths(pr.diff)
    lower_diff = pr.diff.lower()
    risks: list[str] = []
    suggestions: list[str] = []

    if pr.changed_files > 20 or pr.additions + pr.deletions > 1200:
        risks.append("Large change surface; reviewers may miss regressions without focused tests.")
        suggestions.append("Split unrelated changes or add a concise risk-focused test plan.")
    if any(p.endswith(("requirements.txt", "package-lock.json", "pnpm-lock.yaml", "poetry.lock")) for p in paths):
        risks.append("Dependency or lockfile changes may introduce supply-chain or compatibility risk.")
        suggestions.append("Document why dependency changes are needed and verify lockfile integrity.")
    if any(p.endswith((".yml", ".yaml")) and ("workflow" in p or ".github" in p) for p in paths):
        risks.append("CI/workflow changes can affect release permissions or secret exposure.")
        suggestions.append("Confirm workflow permissions are least-privilege and secrets are not printed.")
    if re.search(r"password|secret|token|api[_-]?key", lower_diff):
        risks.append("Diff references credential-like terms; accidental secret exposure is possible.")
        suggestions.append("Run secret scanning and keep real credentials in the platform secret store.")
    if re.search(r"rm -rf|drop table|delete from|truncate", lower_diff):
        risks.append("Destructive command or SQL pattern appears in the diff.")
        suggestions.append("Add guardrails, dry-run defaults, and explicit operator confirmation.")
    if "test" not in " ".join(paths).lower() and pr.additions > 50:
        risks.append("No obvious test files changed alongside non-trivial implementation changes.")
        suggestions.append("Add or update tests for the main changed behavior before merge.")

    if not risks:
        risks.append("No major structural risks detected from the diff heuristics.")
    if not suggestions:
        suggestions.append("Keep the PR description updated with validation steps and rollout notes.")

    file_summary = ", ".join(paths[:8]) + (" ..." if len(paths) > 8 else "")
    confidence = "High" if pr.changed_files <= 10 and pr.additions + pr.deletions <= 500 else "Medium"
    if pr.changed_files > 30 or pr.additions + pr.deletions > 2000:
        confidence = "Low"

    return f"""## Claude PR Review

### Summary of changes
This PR, **{pr.title}**, changes {pr.changed_files} file(s) with +{pr.additions}/-{pr.deletions} lines from `{pr.head}` into `{pr.base}`. The most visible changed paths are: {file_summary or 'not available from diff metadata'}.

### Identified risks
{chr(10).join(f'- {r}' for r in risks)}

### Improvement suggestions
{chr(10).join(f'- {s}' for s in suggestions)}

### Confidence score
**{confidence}**

---
Generated by `claude-review` for `{pr.owner}/{pr.repo}#{pr.number}`.
"""


def claude_review(pr: PullRequest) -> str | None:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = f"""Review this GitHub PR and return Markdown with exactly these sections:
## Claude PR Review
### Summary of changes
### Identified risks
### Improvement suggestions
### Confidence score

PR: {pr.owner}/{pr.repo}#{pr.number}
Title: {pr.title}
Stats: {pr.changed_files} files, +{pr.additions}/-{pr.deletions}
Diff excerpt:\n{pr.diff[:12000]}
"""
    body = json.dumps({
        "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
        "max_tokens": 1200,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode())
        chunks = data.get("content") or []
        text = "\n".join(c.get("text", "") for c in chunks if c.get("type") == "text").strip()
        return text or None
    except (urllib.error.URLError, urllib.error.HTTPError):
        return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and emit structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--output", help="Write Markdown to this file")
    parser.add_argument("--use-claude", action="store_true", help="Use Anthropic Claude when ANTHROPIC_API_KEY is set")
    args = parser.parse_args(argv)

    pr = fetch_pr(args.pr)
    review = claude_review(pr) if args.use_claude else None
    if not review:
        review = heuristic_review(pr)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
