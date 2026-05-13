#!/usr/bin/env python3
import argparse
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from urllib.parse import urlparse


def parse_pr_url(url):
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise SystemExit("Expected PR URL like https://github.com/owner/repo/pull/123")
    return match.groups()


def fetch_diff(pr_url):
    owner, repo, number = parse_pr_url(pr_url)
    repo_name = f"{owner}/{repo}"
    try:
        return subprocess.check_output(
            ["gh", "pr", "diff", number, "--repo", repo_name],
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        with urllib.request.urlopen(f"{pr_url}.diff", timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")


def summarize_files(diff):
    files = re.findall(r"^\+\+\+ b/(.+)$", diff, flags=re.MULTILINE)
    extensions = Counter(path.rsplit(".", 1)[-1] if "." in path else "no-ext" for path in files)
    additions = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
    deletions = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
    return files, extensions, additions, deletions


def risks_for(diff, files, additions, deletions):
    risks = []
    lower = diff.lower()
    if any("migration" in f.lower() or "schema" in f.lower() for f in files):
        risks.append("Database or schema files changed; verify migration order and rollback behavior.")
    if "delete" in lower or "drop table" in lower or "truncate" in lower:
        risks.append("Diff includes destructive data language; confirm safeguards and tests around data loss.")
    if any(f.startswith(".github/workflows/") for f in files):
        risks.append("CI workflow changed; verify secrets, permissions, and pull_request behavior.")
    if additions + deletions > 500:
        risks.append("Large diff size increases review risk; split or add high-level test evidence if possible.")
    if not risks:
        risks.append("No obvious high-risk patterns found from the diff alone.")
    return risks


def suggestions_for(diff, files):
    suggestions = []
    if not re.search(r"(test|spec)\.", "\n".join(files), re.IGNORECASE):
        suggestions.append("Add or update tests that cover the changed behavior.")
    if "TODO" in diff or "FIXME" in diff:
        suggestions.append("Resolve or explain TODO/FIXME comments before merge.")
    if any(f.endswith((".md", ".mdx")) for f in files):
        suggestions.append("Preview documentation rendering to catch broken headings, links, or code fences.")
    suggestions.append("Include exact verification commands in the PR description.")
    return suggestions


def confidence(files, additions, deletions):
    if not files:
        return "Low"
    if additions + deletions > 800:
        return "Low"
    if additions + deletions > 250:
        return "Medium"
    return "High"


def render(pr_url, diff):
    files, extensions, additions, deletions = summarize_files(diff)
    file_summary = ", ".join(f"{count} {ext}" for ext, count in extensions.most_common(4)) or "no files"
    risks = risks_for(diff, files, additions, deletions)
    suggestions = suggestions_for(diff, files)
    score = confidence(files, additions, deletions)

    lines = [
        "## PR Review",
        "",
        "### Summary",
        f"This PR changes {len(files)} file(s) with {additions} additions and {deletions} deletions.",
        f"The main touched file types are: {file_summary}. Review source: {pr_url}.",
        "",
        "### Identified Risks",
    ]
    lines.extend(f"- {risk}" for risk in risks)
    lines.append("")
    lines.append("### Improvement Suggestions")
    lines.extend(f"- {suggestion}" for suggestion in suggestions)
    lines.extend(["", f"### Confidence Score: {score}"])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    args = parser.parse_args()
    print(render(args.pr, fetch_diff(args.pr)))


if __name__ == "__main__":
    raise SystemExit(main())
