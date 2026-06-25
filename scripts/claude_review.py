#!/usr/bin/env python3
"""Generate structured Markdown PR reviews from GitHub pull request diffs."""

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
from pathlib import Path


UA = "claude-review/1.0"


@dataclass(frozen=True)
class PRRef:
    owner: str
    repo: str
    number: int


@dataclass
class FileChange:
    path: str
    additions: int = 0
    deletions: int = 0
    hunks: int = 0


def parse_pr_url(url: str) -> PRRef:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:[/?#].*)?$", url)
    if not match:
        raise ValueError("Expected PR URL like https://github.com/owner/repo/pull/123")
    return PRRef(owner=match.group(1), repo=match.group(2), number=int(match.group(3)))


def request(url: str, accept: str, token: str | None = None, data: bytes | None = None, method: str | None = None) -> str:
    headers = {"User-Agent": UA, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_pr(ref: PRRef, token: str | None = None) -> dict:
    url = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/pulls/{ref.number}"
    return json.loads(request(url, "application/vnd.github+json", token=token))


def fetch_diff(ref: PRRef, token: str | None = None) -> str:
    url = f"https://github.com/{ref.owner}/{ref.repo}/pull/{ref.number}.diff"
    return request(url, "application/vnd.github.v3.diff", token=token)


def parse_diff(diff: str) -> list[FileChange]:
    files: list[FileChange] = []
    current: FileChange | None = None
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" b/", 1)
            path = parts[1] if len(parts) == 2 else line.rsplit(" ", 1)[-1]
            current = FileChange(path=path)
            files.append(current)
            continue
        if current is None:
            continue
        if line.startswith("@@"):
            current.hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            current.additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            current.deletions += 1
    return files


def classify_files(files: list[FileChange]) -> dict[str, int]:
    buckets = {
        "tests": 0,
        "docs": 0,
        "scripts": 0,
        "config": 0,
        "source": 0,
    }
    for file in files:
        path = file.path.lower()
        if "test" in path or path.startswith("spec") or path.endswith((".test.ts", ".test.js", "_test.py")):
            buckets["tests"] += 1
        elif path.endswith((".md", ".mdx", ".rst")) or "docs/" in path:
            buckets["docs"] += 1
        elif path.startswith("scripts/") or path.endswith((".sh", ".py")):
            buckets["scripts"] += 1
        elif path.endswith((".yml", ".yaml", ".json", ".toml", ".ini")):
            buckets["config"] += 1
        else:
            buckets["source"] += 1
    return buckets


def summary_sentences(pr: dict, files: list[FileChange]) -> str:
    title = pr.get("title") or f"PR #{pr.get('number')}"
    total_add = sum(f.additions for f in files)
    total_del = sum(f.deletions for f in files)
    changed = len(files)
    buckets = classify_files(files)
    dominant = max(buckets, key=buckets.get) if files else "files"
    sentence_one = f"This PR, \"{title}\", changes {changed} file(s) with +{total_add}/-{total_del} lines."
    shown = ", ".join(f.path for f in files[:4]) if files else "no files"
    if changed > 4:
        shown = f"{shown}, and {changed - 4} more file(s)"
    sentence_two = f"The dominant area is {dominant}, with changes spanning {shown}."
    return sentence_one + " " + sentence_two


def risks(pr: dict, files: list[FileChange], diff: str) -> list[str]:
    output: list[str] = []
    changed = len(files)
    total_add = sum(f.additions for f in files)
    lower = diff.lower()
    buckets = classify_files(files)

    if changed >= 8 or total_add >= 500:
        output.append("Large diff size may hide unrelated changes; confirm the PR stays focused before merge.")
    if buckets["tests"] == 0:
        output.append("No obvious test file changes were detected; verify behavior manually or add focused coverage.")
    if re.search(r"\bdelete\s+from\b|\bdrop\s+table\b|\brm\s+-rf\b|--force\b", lower):
        output.append("Potentially destructive command or SQL text appears in the diff; review execution paths carefully.")
    if any(f.path.endswith((".env", ".pem", ".key")) for f in files) or re.search(r"(api[_-]?key|secret|token)\s*=", lower):
        output.append("Secret-looking configuration appears in the diff; confirm no credentials are committed.")
    if buckets["config"] and buckets["source"]:
        output.append("Config and source changed together; verify local and CI environments use the same assumptions.")
    if not output:
        output.append("No high-risk pattern was detected from the diff shape; still review domain behavior and edge cases.")
    return output


def suggestions(files: list[FileChange], diff: str) -> list[str]:
    output: list[str] = []
    buckets = classify_files(files)
    lower = diff.lower()
    if buckets["tests"] == 0:
        output.append("Add or reference a minimal test/smoke command that proves the main behavior.")
    if "todo" in lower or "fixme" in lower:
        output.append("Resolve or explain TODO/FIXME notes before merge so follow-up work is explicit.")
    if any(f.additions > 200 for f in files):
        output.append("Consider splitting very large files or documenting why the size is necessary.")
    if buckets["docs"] == 0:
        output.append("Add a short usage note if this change introduces a new command, workflow, or public behavior.")
    if not output:
        output.append("Keep the PR description aligned with the changed files and include the exact validation command.")
    return output


def confidence(files: list[FileChange], risks_list: list[str]) -> str:
    if not files:
        return "Low"
    test_present = classify_files(files)["tests"] > 0
    serious = any("destructive" in risk.lower() or "secret" in risk.lower() for risk in risks_list)
    if test_present and not serious:
        return "High"
    if len(files) <= 6 and not serious:
        return "Medium"
    return "Low"


def render_review(pr: dict, files: list[FileChange], diff: str) -> str:
    risks_list = risks(pr, files, diff)
    suggestions_list = suggestions(files, diff)
    confidence_score = confidence(files, risks_list)
    file_lines = [
        f"- `{f.path}` (+{f.additions}/-{f.deletions}, {f.hunks} hunk{'s' if f.hunks != 1 else ''})"
        for f in files[:12]
    ]
    if len(files) > 12:
        file_lines.append(f"- ...and {len(files) - 12} more file(s)")
    if not file_lines:
        file_lines = ["- No changed files detected."]

    lines = [
        "## PR Review",
        "",
        "### Summary of changes",
        summary_sentences(pr, files),
        "",
        "### Changed files",
        *file_lines,
        "",
        "### Identified risks",
        *[f"- {risk}" for risk in risks_list],
        "",
        "### Improvement suggestions",
        *[f"- {suggestion}" for suggestion in suggestions_list],
        "",
        f"### Confidence score: {confidence_score}",
        "",
        "_Generated by `claude-review`._",
    ]
    return "\n".join(lines) + "\n"


def post_comment(ref: PRRef, body: str, token: str) -> str:
    url = f"https://api.github.com/repos/{ref.owner}/{ref.repo}/issues/{ref.number}/comments"
    payload = json.dumps({"body": body}).encode("utf-8")
    response = request(url, "application/vnd.github+json", token=token, data=payload, method="POST")
    return json.loads(response).get("html_url", "")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a structured Markdown review for a GitHub PR.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, e.g. https://github.com/owner/repo/pull/123")
    parser.add_argument("--output", help="Write review Markdown to this file.")
    parser.add_argument("--post-comment", action="store_true", help="Post the review as a GitHub PR comment.")
    parser.add_argument("--token-env", default="GITHUB_TOKEN", help="Env var containing a GitHub token.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        ref = parse_pr_url(args.pr)
        token = os.environ.get(args.token_env)
        pr = fetch_pr(ref, token=token)
        diff = fetch_diff(ref, token=token)
        files = parse_diff(diff)
        review = render_review(pr, files, diff)
        if args.output:
            Path(args.output).write_text(review, encoding="utf-8")
        else:
            print(review, end="")
        if args.post_comment:
            if not token:
                raise RuntimeError(f"--post-comment requires {args.token_env} to be set")
            url = post_comment(ref, review, token)
            print(f"Posted review comment: {url}", file=sys.stderr)
        return 0
    except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
