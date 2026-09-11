#!/usr/bin/env python3
"""Review a GitHub pull request and emit structured Markdown."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)/?$"
)

REVIEW_PROMPT = """You review pull requests for engineering teams.
Read the metadata and diff, then respond with Markdown only (no preamble).

Use exactly these sections and order:

## Summary of changes
2-3 sentences describing what changed and why.

## Identified risks
- bullet list; write "None identified." if appropriate

## Improvement suggestions
- bullet list; write "None." if appropriate

## Confidence score
One line: Low, Medium, or High — plus one short justification sentence.
"""


@dataclass(frozen=True)
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base: str
    head: str
    additions: int
    deletions: int
    changed_files: int
    is_draft: bool
    files: list[dict[str, Any]]
    diff: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_URL_RE.match(url.strip())
    if not match:
        raise SystemExit(f"Invalid PR URL: {url}")
    return match.group("owner"), match.group("repo"), int(match.group("number"))


def run_gh(args: list[str]) -> str:
    command = ["gh", *args]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or "gh command failed"
        raise SystemExit(f"{' '.join(command)}\n{message}")
    return completed.stdout or ""


def load_pull_request(url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(url)
    repo_slug = f"{owner}/{repo}"
    meta = json.loads(
        run_gh(
            [
                "pr",
                "view",
                str(number),
                "--repo",
                repo_slug,
                "--json",
                "title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,isDraft,files",
            ]
        )
    )
    diff = run_gh(["pr", "diff", str(number), "--repo", repo_slug])
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=meta["title"],
        body=(meta.get("body") or "").strip(),
        author=(meta.get("author") or {}).get("login", "unknown"),
        base=meta.get("baseRefName", ""),
        head=meta.get("headRefName", ""),
        additions=int(meta.get("additions") or 0),
        deletions=int(meta.get("deletions") or 0),
        changed_files=int(meta.get("changedFiles") or 0),
        is_draft=bool(meta.get("isDraft")),
        files=list(meta.get("files") or []),
        diff=diff,
    )


def trim_diff(diff: str, max_chars: int = 120_000) -> str:
    if len(diff) <= max_chars:
        return diff
    half = max_chars // 2
    return (
        diff[:half]
        + f"\n\n... diff truncated ({len(diff) - max_chars} chars omitted) ...\n\n"
        + diff[-half:]
    )


def build_context(pr: PullRequest) -> str:
    file_lines = []
    for entry in pr.files[:40]:
        path = entry.get("path", "?")
        additions = entry.get("additions", 0)
        deletions = entry.get("deletions", 0)
        file_lines.append(f"- {path} (+{additions}/-{deletions})")
    if len(pr.files) > 40:
        file_lines.append(f"- ... and {len(pr.files) - 40} more files")

    return (
        f"Repository: {pr.owner}/{pr.repo}\n"
        f"Pull request: #{pr.number}\n"
        f"Title: {pr.title}\n"
        f"Author: {pr.author}\n"
        f"Branch: {pr.head} -> {pr.base}\n"
        f"Draft: {pr.is_draft}\n"
        f"Size: +{pr.additions}/-{pr.deletions} across {pr.changed_files} files\n\n"
        f"Description:\n{pr.body or '(empty)'}\n\n"
        f"Changed files:\n"
        + ("\n".join(file_lines) if file_lines else "(none)")
        + "\n\nDiff:\n"
        + trim_diff(pr.diff)
    )


def anthropic_review(context: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    model = os.environ.get("CLAUDE_REVIEW_MODEL", "claude-sonnet-4-20250514")
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": REVIEW_PROMPT,
        "messages": [{"role": "user", "content": context}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {error.code}: {detail}") from error

    parts = body.get("content") or []
    text = "".join(part.get("text", "") for part in parts if part.get("type") == "text")
    if not text.strip():
        raise RuntimeError("Anthropic API returned empty review")
    return text.strip()


def heuristic_review(pr: PullRequest) -> str:
    risks: list[str] = []
    suggestions: list[str] = []

    if pr.is_draft:
        risks.append("Pull request is still marked as draft.")
    if pr.additions + pr.deletions > 2000:
        risks.append("Large change set; review coverage and rollback plan carefully.")
    if pr.changed_files > 25:
        risks.append("Many files touched; regression risk is elevated.")

    paths = [str(entry.get("path", "")) for entry in pr.files]
    joined = "\n".join(paths)
    if any(token in joined for token in ("migration", "migrations/", "schema")):
        risks.append("Schema or migration changes detected.")
        suggestions.append("Document migration rollout and backward compatibility.")
    if any(token in joined for token in (".github/workflows", "Dockerfile", "docker-compose")):
        risks.append("CI or deployment configuration changed.")
    if any(token in joined.lower() for token in ("auth", "token", "password", "secret")):
        risks.append("Authentication or secret-handling code changed.")
    if "test" not in joined.lower() and pr.additions > 80:
        suggestions.append("Add or update automated tests for new behavior.")

    diff_lower = pr.diff.lower()
    if "todo" in diff_lower or "fixme" in diff_lower:
        suggestions.append("Resolve TODO/FIXME markers before merge.")
    if "print(" in pr.diff or "console.log" in pr.diff:
        suggestions.append("Remove debug logging before merge.")

    if not risks:
        risks.append("None identified from static heuristics.")
    if not suggestions:
        suggestions.append("None.")

    size = pr.additions + pr.deletions
    if pr.is_draft or size > 2500 or len(paths) > 30:
        confidence = "Low"
        confidence_reason = "Draft status or very large surface area."
    elif size > 700 or any(token in joined for token in ("migration", "auth", "workflow")):
        confidence = "Medium"
        confidence_reason = "Moderate size or sensitive areas touched."
    else:
        confidence = "High"
        confidence_reason = "Small, focused diff with limited blast radius."

    summary = (
        f"This PR ({pr.head} -> {pr.base}) updates {pr.changed_files} file(s) "
        f"with +{pr.additions}/-{pr.deletions} lines. "
        f"The stated intent is: {pr.title}."
    )
    if pr.body:
        summary += f" The description adds: {pr.body.splitlines()[0][:180]}"

    return (
        "## Summary of changes\n"
        f"{summary}\n\n"
        "## Identified risks\n"
        + "\n".join(f"- {item}" for item in risks)
        + "\n\n## Improvement suggestions\n"
        + "\n".join(f"- {item}" for item in suggestions)
        + f"\n\n## Confidence score\n{confidence} — {confidence_reason}"
    )


def render_markdown(pr: PullRequest, review_body: str) -> str:
    header = (
        f"# PR Review: {pr.owner}/{pr.repo}#{pr.number}\n\n"
        f"**Title:** {pr.title}\n\n"
        f"**Author:** @{pr.author}\n\n"
        f"**Diff size:** +{pr.additions}/-{pr.deletions} in {pr.changed_files} file(s)\n\n"
    )
    return header + review_body.strip() + "\n"


def review_pull_request(url: str, offline: bool = False) -> str:
    pr = load_pull_request(url)
    if offline:
        body = heuristic_review(pr)
    else:
        try:
            body = anthropic_review(build_context(pr))
        except RuntimeError:
            body = heuristic_review(pr)
    return render_markdown(pr, body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request.")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip Anthropic API and use built-in heuristics only",
    )
    parser.add_argument(
        "--output",
        help="Write Markdown review to this file instead of stdout",
    )
    args = parser.parse_args()

    markdown = review_pull_request(args.pr, offline=args.offline)
    if args.output:
        with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(markdown)
    else:
        sys.stdout.write(markdown)


if __name__ == "__main__":
    main()
