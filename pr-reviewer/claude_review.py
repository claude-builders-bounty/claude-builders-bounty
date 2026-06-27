#!/usr/bin/env python3
"""
claude-review — AI-assisted GitHub PR reviewer.

Fetches a PR diff, builds a rich analysis prompt, and outputs a structured
Markdown review. Designed to run as a Claude Code sub-agent or standalone CLI.

Usage:
  python claude_review.py --pr https://github.com/owner/repo/pull/123
  python claude_review.py --pr owner/repo/123   # shorthand
  python claude_review.py --pr 123 --repo owner/repo
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
from typing import Any


# ---------------------------------------------------------------------------
# GitHub client (zero external dependencies)
# ---------------------------------------------------------------------------

class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str | None = None) -> None:
        self._token = token or os.environ.get("GITHUB_TOKEN")

    def _get(self, path: str, accept: str = "application/vnd.github+json") -> Any:
        url = f"{self.BASE}{path}"
        req = urllib.request.Request(url, headers={
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {self._token}"} if self._token else {}),
            "User-Agent": "claude-review/1.0",
        })
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API {exc.code}: {body[:300]}") from exc

    def get_pr(self, owner: str, repo: str, number: int) -> dict:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}")

    def get_pr_files(self, owner: str, repo: str, number: int) -> list[dict]:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}/files")

    def get_pr_commits(self, owner: str, repo: str, number: int) -> list[dict]:
        return self._get(f"/repos/{owner}/{repo}/pulls/{number}/commits")

    def get_pr_diff(self, owner: str, repo: str, number: int) -> str:
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{number}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.diff",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": f"Bearer {self._token}"} if self._token else {}),
            "User-Agent": "claude-review/1.0",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Risk heuristics (no LLM needed for structural analysis)
# ---------------------------------------------------------------------------

_SECURITY_SENSITIVE = {
    ".env", ".pem", ".key", ".crt", ".p12", ".pfx",
    "secret", "password", "credential", "token", "auth",
    "private_key", "api_key", "access_key",
}

_INFRA_FILES = {
    "dockerfile", "docker-compose", ".github/workflows",
    "terraform", ".tf", "kubernetes", "k8s",
    "deploy", "ci", "cd",
}

_TEST_EXTS = {".test.", ".spec.", "_test.", "_spec.", "test_", "spec_"}


def _file_risk_score(filename: str, additions: int, deletions: int) -> tuple[int, list[str]]:
    """Return (0-3 risk level, list of risk reasons) for a changed file."""
    fname_lower = filename.lower()
    risks = []
    score = 0

    if any(s in fname_lower for s in _SECURITY_SENSITIVE):
        risks.append(f"`{filename}` — security-sensitive file (credentials/keys)")
        score += 3

    if any(s in fname_lower for s in _INFRA_FILES):
        risks.append(f"`{filename}` — infrastructure/CI change")
        score += 2

    if additions + deletions > 200:
        risks.append(f"`{filename}` — large change ({additions}+ lines added)")
        score += 1

    return min(score, 3), risks


def analyze_pr(pr: dict, files: list[dict], commits: list[dict]) -> dict:
    """Structural analysis without LLM: count signals, identify risks."""
    total_additions = sum(f.get("additions", 0) for f in files)
    total_deletions = sum(f.get("deletions", 0) for f in files)

    file_types: dict[str, int] = {}
    risks: list[str] = []
    has_tests = False
    max_file_change = 0

    for f in files:
        ext = os.path.splitext(f.get("filename", ""))[1].lower()
        file_types[ext] = file_types.get(ext, 0) + 1
        fname = f.get("filename", "").lower()

        if any(t in fname for t in _TEST_EXTS) or fname.startswith("test") or "/test" in fname:
            has_tests = True

        change_size = f.get("additions", 0) + f.get("deletions", 0)
        max_file_change = max(max_file_change, change_size)

        _, file_risks = _file_risk_score(fname, f.get("additions", 0), f.get("deletions", 0))
        risks.extend(file_risks)

    # PR-level risks
    if len(files) > 20:
        risks.append(f"Large PR scope ({len(files)} files changed) — consider splitting")
    if total_additions > 500:
        risks.append(f"Large addition volume ({total_additions} lines) — review fatigue risk")
    if not has_tests and total_additions > 50:
        risks.append("No test file changes detected — consider adding tests")
    if not pr.get("body"):
        risks.append("PR has no description — context for reviewers is missing")

    # Confidence scoring
    confidence_signals = 0
    if pr.get("body"):
        confidence_signals += 1
    if has_tests:
        confidence_signals += 1
    if len(commits) > 0 and all(c.get("commit", {}).get("message", "").strip() for c in commits):
        confidence_signals += 1
    if len(files) <= 10:
        confidence_signals += 1
    if total_additions < 200:
        confidence_signals += 1

    if confidence_signals >= 4:
        confidence = "High"
    elif confidence_signals >= 2:
        confidence = "Medium"
    else:
        confidence = "Low"

    return {
        "total_files": len(files),
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "file_types": file_types,
        "has_tests": has_tests,
        "risks": risks,
        "confidence": confidence,
        "commit_count": len(commits),
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def _top_extensions(file_types: dict[str, int], n: int = 5) -> str:
    sorted_types = sorted(file_types.items(), key=lambda x: -x[1])
    return ", ".join(f"`{ext or 'no-ext'}`" for ext, _ in sorted_types[:n]) or "unknown"


def generate_report(pr: dict, files: list[dict], commits: list[dict], analysis: dict,
                    pr_url: str) -> str:
    """Produce the structured Markdown review."""
    title = pr.get("title", "(untitled)")
    author = pr.get("user", {}).get("login", "unknown")
    base = pr.get("base", {}).get("ref", "?")
    head = pr.get("head", {}).get("ref", "?")
    body = (pr.get("body") or "").strip()
    body_excerpt = textwrap.shorten(body, width=200, placeholder="…") if body else "_No description provided._"

    # Summarize changed files concisely
    file_list = "\n".join(
        f"- `{f['filename']}` (+{f.get('additions',0)} −{f.get('deletions',0)})"
        for f in sorted(files, key=lambda f: -(f.get("additions",0)+f.get("deletions",0)))[:8]
    )
    if len(files) > 8:
        file_list += f"\n- _(and {len(files) - 8} more files)_"

    # Commit messages
    commit_msgs = "\n".join(
        f"- `{c['sha'][:7]}` {c.get('commit',{}).get('message','').splitlines()[0][:80]}"
        for c in commits[:5]
    )
    if len(commits) > 5:
        commit_msgs += f"\n- _(and {len(commits)-5} more commits)_"

    # Risks section
    risks_section = (
        "\n".join(f"- ⚠️ {r}" for r in analysis["risks"])
        if analysis["risks"]
        else "- ✅ No structural risks detected."
    )

    # Improvements (static heuristics)
    improvements = []
    if not analysis["has_tests"]:
        improvements.append("Add unit tests for the changed logic to prevent regressions.")
    if not body:
        improvements.append("Add a PR description explaining the motivation and approach.")
    if analysis["total_files"] > 15:
        improvements.append("Consider splitting this PR into smaller, focused changes.")
    if any(f.get("additions", 0) > 300 for f in files):
        large = next(f for f in files if f.get("additions", 0) > 300)
        improvements.append(f"Break up `{large['filename']}` — large files are hard to review.")
    if not improvements:
        improvements.append("Code structure looks clean based on file analysis.")

    improvements_section = "\n".join(f"- 💡 {i}" for i in improvements)

    lines = [
        f"## PR Review: [{title}]({pr_url})",
        "",
        f"> **{author}** wants to merge `{head}` → `{base}`  ",
        f"> {analysis['commit_count']} commit(s) · {analysis['total_files']} file(s) changed · "
        f"+{analysis['total_additions']} −{analysis['total_deletions']} lines",
        "",
        "---",
        "",
        "### Summary",
        "",
        f"{body_excerpt}",
        "",
        f"This PR touches {analysis['total_files']} file(s), primarily "
        f"{_top_extensions(analysis['file_types'])}. "
        f"{'Tests are included.' if analysis['has_tests'] else 'No test changes detected.'}",
        "",
        "**Changed files (top by size):**",
        "",
        file_list,
        "",
        "**Commits:**",
        "",
        commit_msgs,
        "",
        "---",
        "",
        "### Identified Risks",
        "",
        risks_section,
        "",
        "---",
        "",
        "### Improvement Suggestions",
        "",
        improvements_section,
        "",
        "---",
        "",
        f"### Confidence Score: **{analysis['confidence']}**",
        "",
    ]

    confidence_details = []
    if pr.get("body"):
        confidence_details.append("has a description")
    if analysis["has_tests"]:
        confidence_details.append("includes tests")
    if analysis["total_files"] <= 10:
        confidence_details.append("has focused scope")
    if analysis["commit_count"] > 0:
        confidence_details.append("has descriptive commits")
    if not analysis["risks"]:
        confidence_details.append("no structural risks found")

    if confidence_details:
        lines.append(f"_This PR {', '.join(confidence_details[:3])}._")
    else:
        lines.append("_Confidence is low — the PR lacks description, tests, or has a broad scope. Manual review is strongly recommended._")

    lines += ["", "---", "", "_Generated by [claude-review](https://github.com/castrocrest/claude-builders-bounty-entries)_"]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_pr_url(pr_arg: str, repo_arg: str | None) -> tuple[str, str, int]:
    """Parse various PR URL formats into (owner, repo, number)."""
    # Full GitHub URL
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_arg)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # owner/repo/number
    m = re.match(r"([^/]+)/([^/]+)/(\d+)$", pr_arg)
    if m:
        return m.group(1), m.group(2), int(m.group(3))

    # Just a number, needs --repo
    if pr_arg.isdigit():
        if not repo_arg:
            raise ValueError("Provide --repo owner/name when using a bare PR number")
        parts = repo_arg.split("/")
        if len(parts) != 2:
            raise ValueError("--repo must be in owner/name format")
        return parts[0], parts[1], int(pr_arg)

    raise ValueError(f"Cannot parse PR reference: {pr_arg!r}")


def _err(msg: str) -> None:
    sys.stderr.write(f"[claude-review] {msg}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review a GitHub PR and output structured Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_review.py --pr https://github.com/psf/requests/pull/7500
  python claude_review.py --pr psf/requests/7500
  python claude_review.py --pr 7500 --repo psf/requests
""",
    )
    parser.add_argument("--pr", required=True, help="GitHub PR URL, owner/repo/number, or just number")
    parser.add_argument("--repo", help="Repository in owner/name format (needed with bare PR number)")
    parser.add_argument("--token", help="GitHub PAT (or set GITHUB_TOKEN env var)")
    parser.add_argument("--output", help="Save output to FILE instead of stdout")
    args = parser.parse_args()

    try:
        owner, repo, number = _parse_pr_url(args.pr, args.repo)
    except ValueError as exc:
        parser.error(str(exc))

    pr_url = f"https://github.com/{owner}/{repo}/pull/{number}"
    client = GitHubClient(token=args.token)

    _err(f"Fetching PR #{number} from {owner}/{repo}...")
    try:
        pr = client.get_pr(owner, repo, number)
        files = client.get_pr_files(owner, repo, number)
        commits = client.get_pr_commits(owner, repo, number)
    except RuntimeError as exc:
        _err(f"Error: {exc}")
        sys.exit(1)

    _err(f"Analyzing {len(files)} changed files, {len(commits)} commits...")
    analysis = analyze_pr(pr, files, commits)
    report = generate_report(pr, files, commits, analysis, pr_url)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report + "\n")
        _err(f"Saved to {args.output}")
    else:
        print(report)


if __name__ == "__main__":
    main()
