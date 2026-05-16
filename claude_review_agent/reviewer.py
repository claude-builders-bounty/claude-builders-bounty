"""Deterministic PR review engine for the Onyx Claude Code sub-agent.

The CLI can run anywhere Python 3.10+ is available. It fetches a pull request
diff, scans for common review risks, and emits a structured Markdown comment.
"""

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
from typing import Iterable


PR_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/pull/(\d+)")


@dataclass
class Finding:
    level: str
    message: str


@dataclass
class Review:
    pr_url: str
    files_changed: int
    additions: int
    deletions: int
    summary: list[str]
    risks: list[Finding]
    suggestions: list[str]
    confidence: str


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.fullmatch(url.strip())
    if not match:
        raise ValueError("Expected PR URL shaped like https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)


def request_text(url: str, accept: str = "application/vnd.github.v3.diff") -> str:
    headers = {
        "Accept": accept,
        "User-Agent": "Onyx-Claude-Review-Agent/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_pr_diff(pr_url: str) -> str:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    return request_text(api_url)


def fetch_pr_metadata(pr_url: str) -> dict:
    owner, repo, number = parse_pr_url(pr_url)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    payload = request_text(api_url, accept="application/vnd.github+json")
    return json.loads(payload)


def read_diff_from_git(base: str) -> str:
    result = subprocess.run(
        ["git", "diff", "--unified=80", base],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout


def changed_files(diff: str) -> list[str]:
    return [line.removeprefix("diff --git a/").split(" b/", 1)[0] for line in diff.splitlines() if line.startswith("diff --git ")]


def changed_lines(diff: str) -> tuple[list[str], int, int]:
    added: list[str] = []
    additions = 0
    deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
            added.append(line[1:])
        elif line.startswith("-"):
            deletions += 1
    return added, additions, deletions


def contains_any(text: str, needles: Iterable[str]) -> bool:
    lower = text.lower()
    return any(needle in lower for needle in needles)


def ascii_safe(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2026": "...",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value.encode("ascii", errors="ignore").decode("ascii")


def risk_scan(files: list[str], added: list[str], additions: int, deletions: int) -> list[Finding]:
    text = "\n".join(added)
    risks: list[Finding] = []

    if additions + deletions > 700:
        risks.append(Finding("High", "Large diff size increases review risk; split or document migration boundaries."))
    elif additions + deletions > 250:
        risks.append(Finding("Medium", "Moderate diff size; focus manual review on behavior changes and edge cases."))

    if contains_any(text, ["eval(", "exec(", "subprocess", "shell=true", "child_process.exec"]):
        risks.append(Finding("High", "Command execution or dynamic evaluation appears in added code. Verify input sanitization and least privilege."))

    if contains_any(text, ["api_key", "secret", "token", "password", "private_key"]):
        risks.append(Finding("Medium", "Credential-like terms appear in added lines. Confirm no secrets are committed and env vars are documented."))

    if contains_any(text, ["todo", "fixme", "hack"]):
        risks.append(Finding("Medium", "TODO/FIXME/HACK markers remain in changed code. Confirm they are intentional before merge."))

    if any(path.startswith(".github/workflows/") for path in files):
        risks.append(Finding("Medium", "GitHub Actions workflow changed. Review permissions, checkout depth, token scopes, and third-party actions."))

    if any(path.endswith((".sql", ".prisma")) or "migration" in path.lower() for path in files):
        risks.append(Finding("Medium", "Database schema or migration file changed. Confirm rollback path and production data safety."))

    if any(path.endswith((".md", ".mdx")) for path in files) and not any(not path.endswith((".md", ".mdx")) for path in files):
        risks.append(Finding("Low", "Documentation-only change. Main risk is accuracy and broken links rather than runtime behavior."))

    if not risks:
        risks.append(Finding("Low", "No obvious risk patterns detected from the diff. Manual review should still verify intent and tests."))
    return risks


def suggestion_scan(files: list[str], added: list[str], risks: list[Finding]) -> list[str]:
    text = "\n".join(added).lower()
    suggestions: list[str] = []

    if not any(("test" in path.lower() or "spec" in path.lower()) for path in files):
        suggestions.append("Add or link to tests that cover the changed behavior, even if the code path looks small.")
    if any(f.level == "High" for f in risks):
        suggestions.append("Add a short security note in the PR description explaining how high-risk paths are guarded.")
    if "readme" not in text and not any(path.lower().endswith("readme.md") for path in files):
        suggestions.append("Update usage or operational docs if this changes user-visible behavior.")
    if any(path.startswith(".github/workflows/") for path in files):
        suggestions.append("Pin action permissions explicitly and avoid broad default GitHub token scopes.")
    if not suggestions:
        suggestions.append("Keep the PR description focused on what changed, why it changed, and how it was verified.")
    return suggestions


def make_summary(metadata: dict | None, files: list[str], additions: int, deletions: int) -> list[str]:
    title = ascii_safe(metadata.get("title", "")) if metadata else None
    prefix = f"This PR updates {len(files)} file(s) with {additions} additions and {deletions} deletions."
    if title:
        prefix = f"`{title}` updates {len(files)} file(s) with {additions} additions and {deletions} deletions."
    files_hint = ", ".join(files[:4]) if files else "no files detected"
    if len(files) > 4:
        files_hint += f", and {len(files) - 4} more"
    return [
        prefix,
        f"The main review surface is: {files_hint}. Onyx focused this pass on risky patterns, missing verification, and merge-readiness signals.",
    ]


def confidence_for(files: list[str], additions: int, deletions: int, risks: list[Finding]) -> str:
    total = additions + deletions
    if any(f.level == "High" for f in risks) or total > 700:
        return "Low"
    if total > 250 or len(files) > 8 or any(f.level == "Medium" for f in risks):
        return "Medium"
    return "High"


def analyze(pr_url: str, diff: str, metadata: dict | None = None) -> Review:
    files = changed_files(diff)
    added, additions, deletions = changed_lines(diff)
    risks = risk_scan(files, added, additions, deletions)
    suggestions = suggestion_scan(files, added, risks)
    return Review(
        pr_url=pr_url,
        files_changed=len(files),
        additions=additions,
        deletions=deletions,
        summary=make_summary(metadata, files, additions, deletions),
        risks=risks,
        suggestions=suggestions,
        confidence=confidence_for(files, additions, deletions, risks),
    )


def render_markdown(review: Review) -> str:
    lines = [
        "## Onyx PR Review",
        "",
        "### Summary of changes",
        "",
        *[f"- {item}" for item in review.summary],
        "",
        "### Identified risks",
        "",
        *[f"- **{finding.level}:** {finding.message}" for finding in review.risks],
        "",
        "### Improvement suggestions",
        "",
        *[f"- {item}" for item in review.suggestions],
        "",
        f"### Confidence score: {review.confidence}",
        "",
        "<sub>Generated by Onyx, a BCC Claude Code review agent. Human approval is still recommended before merge.</sub>",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub pull request.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--diff-file", help="Read a saved diff instead of fetching from GitHub.")
    parser.add_argument("--local-base", help="Review local git diff against this base, e.g. origin/main.")
    parser.add_argument("--output", help="Write Markdown review to this file instead of stdout.")
    args = parser.parse_args(argv)

    try:
        metadata = None
        if args.diff_file:
            diff = open(args.diff_file, "r", encoding="utf-8").read()
        elif args.local_base:
            diff = read_diff_from_git(args.local_base)
        else:
            metadata = fetch_pr_metadata(args.pr)
            diff = fetch_pr_diff(args.pr)
        markdown = render_markdown(analyze(args.pr, diff, metadata))
    except (OSError, ValueError, urllib.error.URLError, subprocess.CalledProcessError) as exc:
        print(f"claude-review failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(markdown + "\n")
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
