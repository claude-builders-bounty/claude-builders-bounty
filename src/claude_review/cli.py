from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


PR_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/.*)?$")


@dataclass
class PullRequest:
    owner: str
    repo: str
    number: int
    title: str
    url: str
    diff: str


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = PR_RE.match(url.strip())
    if not match:
        raise ValueError("PR URL must look like https://github.com/owner/repo/pull/123")
    owner, repo, number = match.groups()
    return owner, repo, int(number)


def _request(url: str, accept: str) -> bytes:
    headers = {
        "Accept": accept,
        "User-Agent": "claude-review/0.1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc.reason}") from exc


def fetch_pr(pr_url: str) -> PullRequest:
    owner, repo, number = parse_pr_url(pr_url)
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    metadata = json.loads(_request(api, "application/vnd.github+json").decode("utf-8"))
    diff = _request(api, "application/vnd.github.v3.diff").decode("utf-8", errors="replace")
    return PullRequest(
        owner=owner,
        repo=repo,
        number=number,
        title=str(metadata.get("title") or f"PR #{number}"),
        url=str(metadata.get("html_url") or pr_url),
        diff=diff,
    )


def _changed_files(diff: str) -> list[str]:
    files = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.append(line[6:].strip())
    return files


def _stats(diff: str) -> tuple[int, int]:
    additions = deletions = 0
    for line in diff.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1
    return additions, deletions


def deterministic_review(pr: PullRequest) -> str:
    files = _changed_files(pr.diff)
    additions, deletions = _stats(pr.diff)
    lowered = pr.diff.lower()

    code_exts = (".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb", ".php")
    code_changed = any(path.endswith(code_exts) for path in files)
    tests_changed = any("test" in path.lower() for path in files)
    docs_only = bool(files) and all(
        path.lower().endswith((".md", ".rst", ".txt")) or "/docs/" in f"/{path.lower()}/"
        for path in files
    )

    risks: list[str] = []
    suggestions: list[str] = []

    security_terms = ("auth", "token", "password", "cookie", "permission", "secret", "digest")
    if any(term in lowered for term in security_terms):
        risks.append("The diff touches authentication or security-sensitive behavior; regressions could affect request integrity or access control.")
        suggestions.append("Add focused regression tests for malformed, empty, and boundary inputs around the security-sensitive path.")

    if code_changed and not tests_changed:
        risks.append("Production code changes are not accompanied by an obvious test-file change in this diff.")
        suggestions.append("Add or extend automated tests that fail before the change and pass after it.")

    if docs_only:
        risks.append("Documentation examples can drift from actual runtime behavior if they are not exercised by doctests or documentation tests.")
        suggestions.append("Run the documentation test/build pipeline and verify copied examples against the current API.")

    if additions + deletions > 300:
        risks.append("The change is relatively large, which increases review surface and the chance of unrelated regressions.")
        suggestions.append("Consider splitting independent concerns into smaller pull requests or commits.")

    if not risks:
        risks.append("No high-risk pattern is obvious from the diff alone; hidden integration or environment-specific regressions may still exist.")
    if not suggestions:
        suggestions.append("Run the repository's relevant unit/integration tests and verify edge cases for the changed behavior.")

    file_text = ", ".join(files[:4]) if files else "the submitted diff"
    if len(files) > 4:
        file_text += f", and {len(files) - 4} more"

    summary = (
        f"This PR changes {file_text}, with approximately {additions} added and {deletions} removed lines. "
        f"The main intent appears to be: {pr.title.rstrip('.')}. "
        "The review below focuses on regression risk, test coverage, and maintainability visible from the diff."
    )

    confidence = "High"
    if additions + deletions > 500:
        confidence = "Low"
    elif additions + deletions > 120 or not files:
        confidence = "Medium"

    risk_md = "\n".join(f"- {item}" for item in risks)
    suggestion_md = "\n".join(f"- {item}" for item in suggestions)

    return (
        "## Claude Code PR Review\n\n"
        f"> **PR:** [{pr.owner}/{pr.repo}#{pr.number}]({pr.url}) — {pr.title}\n\n"
        "### Summary\n"
        f"{summary}\n\n"
        "### Identified Risks\n"
        f"{risk_md}\n\n"
        "### Improvement Suggestions\n"
        f"{suggestion_md}\n\n"
        f"### Confidence: {confidence}\n"
    )


def claude_review(pr: PullRequest) -> str | None:
    claude = shutil.which("claude")
    if not claude:
        return None
    prompt = (
        "Review this GitHub PR diff. Return Markdown with exactly these sections: "
        "Summary (2-3 sentences), Identified Risks (list), Improvement Suggestions (list), "
        "Confidence: Low/Medium/High. Be concise and do not invent facts.\n\n"
        f"PR: {pr.url}\nTitle: {pr.title}\n\nDIFF:\n{pr.diff[:120000]}"
    )
    try:
        proc = subprocess.run(
            [claude, "-p", prompt],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    text = proc.stdout.strip()
    if proc.returncode == 0 and text:
        return text
    return None


def build_review(pr: PullRequest, force_offline: bool = False) -> str:
    if not force_offline:
        generated = claude_review(pr)
        if generated:
            return generated
    return deterministic_review(pr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub pull request as structured Markdown.")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    parser.add_argument("--offline", action="store_true", help="Use deterministic local reviewer even if Claude Code is installed")
    parser.add_argument("--output", help="Write Markdown to this file instead of stdout")
    args = parser.parse_args(argv)

    try:
        pr = fetch_pr(args.pr)
        review = build_review(pr, force_offline=args.offline)
    except (ValueError, RuntimeError) as exc:
        parser.error(str(exc))
        return 2

    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(review)
    else:
        print(review, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
