#!/usr/bin/env python3
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


AGENT_PROMPT_PATH = Path(__file__).with_name("pr-review-agent.md")
MAX_DIFF_CHARS = 50000


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int


def parse_pr_url(url):
    match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/pull/([0-9]+)(?:[/?#].*)?$", url)
    if not match:
        raise ValueError("Expected a GitHub pull request URL like https://github.com/owner/repo/pull/123")
    return PullRequestRef(owner=match.group(1), repo=match.group(2), number=int(match.group(3)))


def github_request(url, accept="application/vnd.github+json"):
    headers = {
        "Accept": accept,
        "User-Agent": "claude-pr-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub request failed: {exc.code} {detail}") from exc


def fetch_pr(pr_ref):
    api_base = f"https://api.github.com/repos/{pr_ref.owner}/{pr_ref.repo}/pulls/{pr_ref.number}"
    pr = json.loads(github_request(api_base))
    files = json.loads(github_request(f"{api_base}/files?per_page=100"))
    diff = github_request(api_base, accept="application/vnd.github.v3.diff")
    return {
        "title": pr.get("title", ""),
        "body": pr.get("body") or "",
        "author": (pr.get("user") or {}).get("login", ""),
        "base": (pr.get("base") or {}).get("ref", ""),
        "head": (pr.get("head") or {}).get("ref", ""),
        "changed_files": [item.get("filename", "") for item in files if item.get("filename")],
        "diff": diff,
    }


def summarize_diff(diff):
    added = 0
    removed = 0
    files = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            parts = line.split(" ")
            if len(parts) >= 4:
                files.append(parts[3][2:])
        elif line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return files, added, removed


def risk_hints(diff, changed_files):
    lowered = diff.lower()
    hints = []
    if any(name.endswith((".sql", "migration.sql")) or "/migrations/" in name for name in changed_files):
        hints.append("Database migration changes need rollback and data-shape review.")
    if any(name.endswith((".yml", ".yaml")) or ".github/workflows/" in name for name in changed_files):
        hints.append("CI or workflow changes can affect release automation and secrets handling.")
    if any(term in lowered for term in ("token", "secret", "password", "api_key", "authorization")):
        hints.append("Credential or authorization-related code appears in the diff.")
    destructive_patterns = (r"\brm\s+-[a-z]*r[a-z]*f", r"\bdrop\s+table\b", r"\btruncate\b", r"\bdelete\s+from\b")
    if any(re.search(pattern, lowered) for pattern in destructive_patterns):
        hints.append("Destructive data or file operations appear in the diff.")
    if not any("test" in name.lower() or "spec" in name.lower() for name in changed_files):
        hints.append("No test files were changed with the implementation.")
    return hints or ["No major risk signals were detected from the diff shape alone."]


def suggestion_hints(diff, changed_files):
    suggestions = []
    if not any("test" in name.lower() or "spec" in name.lower() for name in changed_files):
        suggestions.append("Add focused tests that cover the changed behavior before merging.")
    if len(changed_files) > 8:
        suggestions.append("Consider splitting unrelated changes so reviewers can reason about each part.")
    if any(name.endswith((".md", ".mdx")) for name in changed_files):
        suggestions.append("Check rendered Markdown for broken links, headings, and copy-paste commands.")
    if "todo" in diff.lower():
        suggestions.append("Resolve or track TODO comments before release.")
    return suggestions or ["Review the touched files manually and run the project's normal verification commands."]


def confidence_for(diff, changed_files):
    if len(diff) > 30000 or len(changed_files) > 12:
        return "Low"
    if not any("test" in name.lower() or "spec" in name.lower() for name in changed_files):
        return "Medium"
    return "High"


def build_offline_review(pr_url, title, changed_files, diff):
    diff_files, added, removed = summarize_diff(diff)
    files = changed_files or diff_files
    visible_files = ", ".join(files[:5]) if files else "the submitted files"
    if len(files) > 5:
        visible_files += f", and {len(files) - 5} more"

    risks = risk_hints(diff, files)
    suggestions = suggestion_hints(diff, files)
    confidence = confidence_for(diff, files)

    lines = [
        "## Summary",
        "",
        f"This PR updates {visible_files}. The diff contains about {added} added lines and {removed} removed lines, so the review should focus on changed behavior rather than repository-wide style.",
        f"The PR title is: `{title}`.",
        "",
        "## Identified Risks",
        "",
    ]
    lines.extend(f"- {item}" for item in risks)
    lines.extend(["", "## Improvement Suggestions", ""])
    lines.extend(f"- {item}" for item in suggestions)
    lines.extend(["", "## Confidence", "", f"Confidence: {confidence}", "", f"Reviewed PR: {pr_url}", ""])
    return "\n".join(lines)


def build_claude_prompt(pr_url, pr_data):
    agent_prompt = AGENT_PROMPT_PATH.read_text(encoding="utf-8")
    diff = pr_data["diff"]
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[Diff truncated for review prompt]\n"

    return textwrap.dedent(
        f"""
        {agent_prompt}

        Review this pull request and return only the structured Markdown review.

        PR URL: {pr_url}
        Title: {pr_data['title']}
        Author: {pr_data['author']}
        Base: {pr_data['base']}
        Head: {pr_data['head']}
        Changed files: {', '.join(pr_data['changed_files'])}

        PR body:
        {pr_data['body']}

        Diff:
        ```diff
        {diff}
        ```
        """
    ).strip()


def run_claude(prompt):
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("Claude Code CLI was not found on PATH. Install it or rerun with --offline.")

    result = subprocess.run(
        [claude, "-p", "--permission-mode", "dontAsk"],
        input=prompt,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Claude Code CLI failed")
    return result.stdout.strip()


def validate_review(markdown):
    required = ("## Summary", "## Identified Risks", "## Improvement Suggestions", "## Confidence")
    missing = [section for section in required if section not in markdown]
    if missing:
        raise RuntimeError(f"Review output missing required sections: {', '.join(missing)}")
    if not re.search(r"Confidence:\s*(Low|Medium|High)", markdown):
        raise RuntimeError("Review output must include Confidence: Low, Medium, or High")


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Review a GitHub PR with Claude Code and print Markdown feedback.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL, for example https://github.com/owner/repo/pull/123")
    parser.add_argument("--output", help="Optional file to write the Markdown review to.")
    parser.add_argument("--offline", action="store_true", help="Use deterministic local review output instead of Claude CLI.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    pr_ref = parse_pr_url(args.pr)
    pr_data = fetch_pr(pr_ref)

    if args.offline:
        review = build_offline_review(args.pr, pr_data["title"], pr_data["changed_files"], pr_data["diff"])
    else:
        review = run_claude(build_claude_prompt(args.pr, pr_data))

    validate_review(review)
    if args.output:
        Path(args.output).write_text(review + "\n", encoding="utf-8")
    print(review)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        sys.exit(1)
