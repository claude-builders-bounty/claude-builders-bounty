#!/usr/bin/env python3
"""Claude-oriented PR review agent.

Fetches a GitHub pull request diff and returns a structured Markdown review.
When ANTHROPIC_API_KEY is present it asks Claude; otherwise it falls back to a
deterministic local reviewer so the workflow remains testable without secrets.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_VERSION = "2023-06-01"
MAX_DIFF_CHARS = 65000


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int

    @property
    def api_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{self.number}"

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


def parse_pr_url(url: str) -> PullRequestRef:
    match = re.match(
        r"^https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)(?:[/?#].*)?$",
        url.strip(),
    )
    if not match:
        raise ValueError("PR must look like https://github.com/owner/repo/pull/123")
    return PullRequestRef(match.group(1), match.group(2), int(match.group(3)))


def request_json(url: str, token: str | None = None) -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def request_text(url: str, token: str | None = None, accept: str = "text/plain") -> str:
    headers = {"Accept": accept, "User-Agent": "claude-review-agent"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_pr(pr: PullRequestRef, token: str | None) -> tuple[dict[str, Any], str]:
    metadata = request_json(pr.api_url, token)
    diff = request_text(metadata["diff_url"], token, "application/vnd.github.v3.diff")
    return metadata, diff


def changed_files(diff: str) -> list[str]:
    return re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)


def diff_stats(diff: str) -> tuple[int, int]:
    additions = 0
    deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1
    return additions, deletions


def build_prompt(metadata: dict[str, Any], diff: str) -> str:
    pr_title = metadata.get("title", "Untitled PR")
    pr_url = metadata.get("html_url", "unknown URL")
    files = changed_files(diff)
    additions, deletions = diff_stats(diff)
    truncated = diff[:MAX_DIFF_CHARS]
    if len(diff) > MAX_DIFF_CHARS:
        truncated += "\n\n[Diff truncated for review context]\n"

    return textwrap.dedent(
        f"""
        You are a senior code reviewer. Review the pull request below and return
        only Markdown using this exact structure:

        ## Summary
        Two or three sentences explaining what changed.

        ## Identified Risks
        - Risk bullets, or "- None found in the supplied diff."

        ## Improvement Suggestions
        - Concrete suggestion bullets, or "- None."

        ## Confidence
        High | Medium | Low

        PR: {pr_url}
        Title: {pr_title}
        Files: {", ".join(files) if files else "unknown"}
        Diff stats: +{additions} -{deletions}

        Diff:
        ```diff
        {truncated}
        ```
        """
    ).strip()


def claude_review(prompt: str, model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "max_tokens": 1200,
        "temperature": 0.2,
        "messages": [{"role": "user", "content": prompt}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "User-Agent": "claude-review-agent",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))
    blocks = result.get("content", [])
    return "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text").strip()


def heuristic_review(metadata: dict[str, Any], diff: str) -> str:
    title = metadata.get("title", "this pull request")
    url = metadata.get("html_url", "")
    files = changed_files(diff)
    additions, deletions = diff_stats(diff)
    file_list = ", ".join(files[:6]) if files else "the supplied files"
    if len(files) > 6:
        file_list += f", and {len(files) - 6} more"

    risks: list[str] = []
    suggestions: list[str] = []
    lowered = diff.lower()

    if not files:
        risks.append("No file list could be extracted from the supplied diff.")
    if additions + deletions > 500:
        risks.append("The diff is relatively large, so review should pay extra attention to hidden coupling and missed edge cases.")
    if any(path.endswith((".sh", ".py", ".js", ".ts")) for path in files) and not re.search(r"test|spec", "\n".join(files), re.I):
        risks.append("The changed executable code does not appear to include nearby automated test coverage.")
        suggestions.append("Add focused tests or fixture-based smoke checks that exercise the main success and failure paths.")
    if re.search(r"delete\s+from(?![\s\S]{0,120}\bwhere\b)", lowered):
        risks.append("A SQL DELETE statement appears without a nearby WHERE clause.")
    if re.search(r"rm\s+-[^\n]*[rf]", lowered):
        risks.append("Shell deletion logic appears in the diff and should be reviewed for path safety.")
    if "api_key" in lowered or "token" in lowered or "secret" in lowered:
        risks.append("The diff references credentials or secret-like configuration; verify no secrets are hard-coded.")
        suggestions.append("Document required environment variables and ensure examples use placeholders only.")
    if any(path.lower().endswith(("readme.md", "validation.md", "sample.md")) for path in files):
        suggestions.append("Keep the sample output and README in sync with the CLI flags so users can copy commands directly.")
    if not suggestions:
        suggestions.append("Consider adding a short validation note with the exact command used to verify the change.")

    if not risks:
        risks.append("None found in the supplied diff.")

    confidence = "High"
    if len(diff) > MAX_DIFF_CHARS or additions + deletions > 500:
        confidence = "Medium"
    if not diff.strip():
        confidence = "Low"

    risk_block = "\n".join(f"- {risk}" for risk in risks)
    suggestion_block = "\n".join(f"- {suggestion}" for suggestion in suggestions)
    return (
        "## Summary\n"
        f'This PR, "{title}", changes {file_list}. The supplied diff shows {additions} '
        f"added lines and {deletions} removed lines, with the main review focus on "
        "whether the implementation, documentation, and validation evidence line up.\n\n"
        "## Identified Risks\n"
        f"{risk_block}\n\n"
        "## Improvement Suggestions\n"
        f"{suggestion_block}\n\n"
        "## Confidence\n"
        f"{confidence}\n\n"
        f"<!-- Reviewed PR: {url} -->"
    )


def validate_sections(markdown: str) -> None:
    required = ["## Summary", "## Identified Risks", "## Improvement Suggestions", "## Confidence"]
    missing = [section for section in required if section not in markdown]
    if missing:
        raise ValueError(f"review output missing required sections: {', '.join(missing)}")
    if not re.search(r"## Confidence\s*\n\s*(High|Medium|Low)\b", markdown):
        raise ValueError("confidence must be exactly Low, Medium, or High")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request with Claude-style structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Anthropic model to use. Default: {DEFAULT_MODEL}")
    parser.add_argument("--offline-diff", help="Read a local diff file instead of fetching from GitHub.")
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout only.")
    parser.add_argument("--heuristic", action="store_true", help="Force local deterministic review even when ANTHROPIC_API_KEY exists.")
    args = parser.parse_args(argv)

    try:
        pr = parse_pr_url(args.pr)
        token = os.environ.get("GITHUB_TOKEN")
        if args.offline_diff:
            metadata = {"title": f"{pr.owner}/{pr.repo} PR #{pr.number}", "html_url": pr.html_url}
            with open(args.offline_diff, "r", encoding="utf-8") as handle:
                diff = handle.read()
        else:
            metadata, diff = fetch_pr(pr, token)

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key and not args.heuristic:
            review = claude_review(build_prompt(metadata, diff), args.model, api_key)
        else:
            review = heuristic_review(metadata, diff)
        validate_sections(review)

        if args.output:
            with open(args.output, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(review + "\n")
        print(review)
        return 0
    except (OSError, ValueError, urllib.error.URLError, KeyError) as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
