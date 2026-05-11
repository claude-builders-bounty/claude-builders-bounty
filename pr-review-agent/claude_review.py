#!/usr/bin/env python3
"""Structured PR review agent for Claude Code workflows.

The CLI fetches a GitHub pull request diff, analyzes changed files and hunks,
and prints a review comment with the required sections:

- Summary of changes
- Identified risks
- Improvement suggestions
- Confidence score

If GITHUB_TOKEN is set and --post-comment is passed, the same Markdown is posted
as a pull request comment.
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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


PR_RE = re.compile(r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/pull/(?P<number>\d+)")


@dataclass
class ChangedFile:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)


@dataclass
class ReviewFacts:
    owner: str
    repo: str
    number: str
    title: str | None
    files: list[ChangedFile]

    @property
    def additions(self) -> int:
        return sum(file.additions for file in self.files)

    @property
    def deletions(self) -> int:
        return sum(file.deletions for file in self.files)


def parse_pr_url(url: str) -> tuple[str, str, str]:
    match = PR_RE.match(url.rstrip("/"))
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.group("owner"), match.group("repo"), match.group("number")


def request_text(url: str, token: str | None = None, method: str = "GET", body: bytes | None = None) -> str:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed with HTTP {exc.code}: {detail}") from exc


def fetch_pr_title(owner: str, repo: str, number: str, token: str | None) -> str | None:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    try:
        data = json.loads(request_text(api_url, token=token))
        title = data.get("title")
        return title if isinstance(title, str) else None
    except Exception:
        return None


def fetch_pr_diff(owner: str, repo: str, number: str, token: str | None) -> str:
    diff_url = f"https://github.com/{owner}/{repo}/pull/{number}.diff"
    return request_text(diff_url, token=token)


def parse_unified_diff(diff_text: str) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    current: ChangedFile | None = None

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            parts = line.split(" b/", 1)
            path = parts[1] if len(parts) == 2 else line.rsplit(" ", 1)[-1]
            current = ChangedFile(path=path)
            continue
        if current is None:
            continue
        if line.startswith("+++ b/"):
            current.path = line[6:]
            continue
        if line.startswith("@@"):
            current.hunks += 1
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
            current.added_lines.append(line[1:])
            continue
        if line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
            current.removed_lines.append(line[1:])

    if current:
        files.append(current)
    return files


def file_kind(path: str) -> str:
    lower = path.lower()
    if lower.endswith((".md", ".mdx", ".rst")):
        return "documentation"
    if lower.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
        return "configuration"
    if "/test" in lower or lower.startswith("test") or lower.endswith(("_test.py", ".test.ts", ".spec.ts")):
        return "tests"
    if lower.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".scala", ".java")):
        return "source"
    if lower.endswith((".sh", ".bash", ".ps1")):
        return "script"
    return "other"


def bullet(text: str) -> str:
    return f"- {text}"


def plural(count: int, one: str, many: str | None = None) -> str:
    return f"{count} {one if count == 1 else many or one + 's'}"


def summarize_files(files: list[ChangedFile]) -> str:
    if not files:
        return "The pull request diff is empty or could not be parsed."

    by_kind: dict[str, int] = {}
    for changed in files:
        by_kind[file_kind(changed.path)] = by_kind.get(file_kind(changed.path), 0) + 1

    dominant = sorted(by_kind.items(), key=lambda item: item[1], reverse=True)[0][0]
    notable = ", ".join(changed.path for changed in files[:4])
    if len(files) > 4:
        notable += f", and {len(files) - 4} more"

    return (
        f"This PR changes {plural(len(files), 'file')} with "
        f"{plural(sum(f.additions for f in files), 'addition')} and "
        f"{plural(sum(f.deletions for f in files), 'deletion')}. "
        f"The diff is mostly {dominant} work, touching {notable}."
    )


def contains_any(lines: Iterable[str], patterns: Iterable[str]) -> bool:
    lowered = "\n".join(lines).lower()
    return any(pattern in lowered for pattern in patterns)


def identify_risks(facts: ReviewFacts) -> list[str]:
    risks: list[str] = []
    files = facts.files
    paths = [changed.path for changed in files]
    all_added = [line for changed in files for line in changed.added_lines]

    if not files:
        return ["No changed files were parsed, so the review cannot validate behavior."]

    total_changed = facts.additions + facts.deletions
    if total_changed > 500:
        risks.append("Large diff size makes regressions harder to spot; split or add targeted verification where possible.")

    if any(file_kind(path) == "source" for path in paths) and not any(file_kind(path) == "tests" for path in paths):
        risks.append("Source code changed without a matching test file in the diff.")

    if any(path.lower().endswith(("package.json", "pnpm-lock.yaml", "package-lock.json", "requirements.txt")) for path in paths):
        risks.append("Dependency or package metadata changed; check lockfile consistency and supply-chain impact.")

    if contains_any(all_added, ("password", "secret", "token", "api_key", "private_key")):
        risks.append("Added lines contain credential-like words; verify no real secrets or unsafe examples were committed.")

    if contains_any(all_added, ("subprocess", "shell=true", "exec(", "eval(", "os.system")):
        risks.append("Added code appears to execute commands or evaluate dynamic input; validate input handling and escaping.")

    if any(file_kind(path) == "configuration" for path in paths):
        risks.append("Configuration files changed; verify local, CI, and production environments still agree.")

    return risks or ["No obvious high-risk patterns were detected from the diff alone."]


def improvement_suggestions(facts: ReviewFacts) -> list[str]:
    suggestions: list[str] = []
    paths = [changed.path for changed in facts.files]

    if any(file_kind(path) == "source" for path in paths):
        suggestions.append("Add or update tests around the changed behavior, including at least one failure-path case.")
    if any(file_kind(path) == "documentation" for path in paths):
        suggestions.append("Check that command snippets in the docs are copy-paste runnable from a clean checkout.")
    if facts.additions + facts.deletions > 250:
        suggestions.append("Call out the riskiest files in the PR description so reviewers can focus their pass.")
    if not any(path.lower().startswith((".github/", "tests/", "test/")) for path in paths):
        suggestions.append("Include explicit verification commands in the PR body if automated tests are not changed.")
    suggestions.append("Confirm the PR body links the issue or product requirement this change is intended to satisfy.")

    deduped: list[str] = []
    for item in suggestions:
        if item not in deduped:
            deduped.append(item)
    return deduped


def confidence_score(facts: ReviewFacts) -> str:
    total_changed = facts.additions + facts.deletions
    if not facts.files:
        return "Low"
    if total_changed > 700 or len(facts.files) > 20:
        return "Low"
    if any(file_kind(path.path) == "source" for path in facts.files) and not any(file_kind(path.path) == "tests" for path in facts.files):
        return "Medium"
    return "High"


def render_review(facts: ReviewFacts) -> str:
    title = facts.title or f"{facts.owner}/{facts.repo}#{facts.number}"
    risks = identify_risks(facts)
    suggestions = improvement_suggestions(facts)
    summary_one = summarize_files(facts.files)
    summary_two = (
        f"The review is based on the public PR diff for "
        f"`{facts.owner}/{facts.repo}#{facts.number}` (`{title}`)."
    )

    lines = [
        "## Claude Review",
        "",
        "### Summary of Changes",
        summary_one,
        summary_two,
        "",
        "### Identified Risks",
        *(bullet(risk) for risk in risks),
        "",
        "### Improvement Suggestions",
        *(bullet(suggestion) for suggestion in suggestions),
        "",
        "### Confidence Score",
        confidence_score(facts),
    ]
    return "\n".join(lines) + "\n"


def post_comment(owner: str, repo: str, number: str, markdown: str, token: str) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
    payload = json.dumps({"body": markdown}).encode("utf-8")
    data = json.loads(request_text(api_url, token=token, method="POST", body=payload))
    return data.get("html_url", "")


def build_review(pr_url: str, diff_text: str | None, token: str | None) -> tuple[ReviewFacts, str]:
    owner, repo, number = parse_pr_url(pr_url)
    diff = diff_text if diff_text is not None else fetch_pr_diff(owner, repo, number, token)
    title = fetch_pr_title(owner, repo, number, token)
    facts = ReviewFacts(owner=owner, repo=repo, number=number, title=title, files=parse_unified_diff(diff))
    return facts, render_review(facts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        description="Generate a structured Markdown review for a GitHub pull request.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
              claude-review --pr https://github.com/owner/repo/pull/123 --diff-file pr.diff
            """
        ),
    )
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--diff-file", help="Read a saved unified diff instead of fetching from GitHub")
    parser.add_argument("--post-comment", action="store_true", help="Post the generated review as a PR comment")
    parser.add_argument("--output", help="Write the Markdown review to a file")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token, defaults to GITHUB_TOKEN")
    args = parser.parse_args(argv)

    diff_text = Path(args.diff_file).read_text(encoding="utf-8") if args.diff_file else None
    facts, markdown = build_review(args.pr, diff_text, args.token)

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.write(markdown)

    if args.post_comment:
        if not args.token:
            raise SystemExit("--post-comment requires --token or GITHUB_TOKEN")
        url = post_comment(facts.owner, facts.repo, facts.number, markdown, args.token)
        print(f"Posted review comment: {url}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
