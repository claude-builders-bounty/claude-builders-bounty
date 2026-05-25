#!/usr/bin/env python3
"""claude-review — PR review agent with structured Markdown output.

Usage:
  export GITHUB_TOKEN=ghp_xxx
  python claude-review.py --pr https://github.com/owner/repo/pull/123
  python claude-review.py --pr 123 --repo owner/repo
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Any

GITHUB_API = "https://api.github.com"


@dataclass
class PRData:
    number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    files: list[dict[str, Any]] = field(default_factory=list)
    commits: list[dict[str, Any]] = field(default_factory=list)


def github_request(path: str) -> dict[str, Any] | list[Any]:
    """Make an authenticated GitHub API request."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable required", file=sys.stderr)
        sys.exit(1)
    
    url = f"{GITHUB_API}{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "claude-review-agent")
    
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"GitHub API error ({e.code}): {e.read().decode()[:200]}", file=sys.stderr)
        sys.exit(1)


def parse_pr_url(url: str) -> tuple[str, int]:
    """Parse a GitHub PR URL into (owner/repo, pr_number)."""
    pattern = r"github\.com/([^/]+/[^/]+)/pull/(\d+)"
    match = re.search(pattern, url)
    if not match:
        print(f"Error: invalid PR URL: {url}", file=sys.stderr)
        sys.exit(1)
    return match.group(1), int(match.group(2))


def fetch_pr_data(repo: str, pr_number: int) -> PRData:
    """Fetch all PR data from GitHub API."""
    pr_data = github_request(f"/repos/{repo}/pulls/{pr_number}")
    pr = PRData(
        number=pr_number,
        title=pr_data.get("title", ""),
        description=pr_data.get("body", "") or "",
        author=pr_data.get("user", {}).get("login", "unknown"),
        base_branch=pr_data.get("base", {}).get("ref", ""),
        head_branch=pr_data.get("head", {}).get("ref", ""),
    )
    
    # Fetch files changed
    files_data = github_request(f"/repos/{repo}/pulls/{pr_number}/files")
    pr.files = [{
        "filename": f.get("filename"),
        "status": f.get("status"),
        "additions": f.get("additions", 0),
        "deletions": f.get("deletions", 0),
        "changes": f.get("changes", 0),
        "patch": (f.get("patch") or "")[:500],
    } for f in (files_data if isinstance(files_data, list) else [])]
    
    # Fetch commits
    commits_data = github_request(f"/repos/{repo}/pulls/{pr_number}/commits")
    pr.commits = [{
        "sha": c.get("sha", "")[:7],
        "message": c.get("commit", {}).get("message", "").split("\n")[0],
        "author": c.get("commit", {}).get("author", {}).get("name", "unknown"),
    } for c in (commits_data if isinstance(commits_data, list) else [])]
    
    return pr


def analyze_pr(pr: PRData) -> dict[str, Any]:
    """Analyze a PR and produce a structured review."""
    total_additions = sum(f["additions"] for f in pr.files)
    total_deletions = sum(f["deletions"] for f in pr.files)
    total_changes = sum(f["changes"] for f in pr.files)
    
    # Detect risk patterns
    risks: list[str] = []
    for f in pr.files:
        patch = f.get("patch", "")
        filename = f["filename"]
        
        # Schema changes
        if "migration" in filename or "schema" in filename:
            risks.append(f"⚠️ **Database change**: `{filename}` — verify migration is backward-compatible")
        
        # Dependency changes
        if filename in ("package.json", "requirements.txt", "go.mod", "Cargo.toml"):
            risks.append(f"⚠️ **Dependency change**: `{filename}` — review for supply-chain risk")
        
        # Security-sensitive files
        if any(x in filename for x in ("auth", "security", "secret", "token", "password", "crypto")):
            risks.append(f"🔐 **Security-sensitive**: `{filename}` — verify authentication/authorization logic")
        
        # Config changes
        if filename in (".env.example", "config", "docker-compose", "terraform"):
            risks.append(f"⚙️ **Configuration change**: `{filename}` — verify no secrets exposed")
        
        # API contract changes
        if any(x in filename for x in ("api", "route", "controller", "handler", "endpoint")):
            risks.append(f"🔌 **API change**: `{filename}` — verify backward compatibility")
        
        # Large files
        if f["changes"] > 200:
            risks.append(f"📏 **Large file**: `{filename}` ({f['changes']} lines) — consider splitting")
        
        # Files with TODO/FIXME/HACK
        if patch and re.search(r"TODO|FIXME|HACK|XXX|WORKAROUND", patch):
            risks.append(f"📝 **Incomplete**: `{filename}` — contains TODO/FIXME markers")
    
    # Detect test coverage
    has_tests = any(
        "test" in f["filename"].lower() or "spec" in f["filename"].lower()
        for f in pr.files
    )
    test_files = [f["filename"] for f in pr.files if "test" in f["filename"].lower() or "spec" in f["filename"].lower()]
    
    # Commit quality
    commit_messages = [c["message"] for c in pr.commits]
    bad_commits = [m for m in commit_messages if len(m) < 10 or m.startswith("wip") or m.startswith("fixup")]
    
    # Risk score
    risk_score = "Low"
    if len(risks) >= 5:
        risk_score = "High"
    elif len(risks) >= 2:
        risk_score = "Medium"
    
    return {
        "summary": f"PR #{pr.number} by **@{pr.author}**: *{pr.title}* — `{pr.base_branch}` ← `{pr.head_branch}`",
        "stats": {
            "files_changed": len(pr.files),
            "additions": total_additions,
            "deletions": total_deletions,
            "total_changes": total_changes,
            "commits": len(pr.commits),
        },
        "description": pr.description[:500] if pr.description else "_No description provided._",
        "risks": risks if risks else ["✅ No significant risks detected"],
        "improvements": [
            "✅ Has tests" if has_tests else "❌ **Missing tests** — add test coverage",
        ] + ([
            f"✅ Test files: {', '.join(test_files)}"
        ] if test_files else []) + ([
            f"⚠️ {len(bad_commits)} commit(s) with unclear messages: {', '.join(bad_commits[:3])}"
        ] if bad_commits else []) + [
            f"📊 PR size: {total_changes} lines across {len(pr.files)} files — "
            + ("good size for review" if total_changes < 300 else "consider splitting into smaller PRs"),
        ],
        "confidence": risk_score,
    }


def format_review(analysis: dict[str, Any]) -> str:
    """Format analysis into structured Markdown."""
    lines = [
        "## 🔍 PR Review",
        "",
        f"### Summary",
        analysis["summary"],
        "",
        f"### Description",
        analysis["description"],
        "",
        "### Stats",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Files Changed | {analysis['stats']['files_changed']} |",
        f"| Additions | {analysis['stats']['additions']} |",
        f"| Deletions | {analysis['stats']['deletions']} |",
        f"| Total Changes | {analysis['stats']['total_changes']} |",
        f"| Commits | {analysis['stats']['commits']} |",
        "",
        "### Identified Risks",
    ]
    for r in analysis["risks"]:
        lines.append(f"- {r}")
    
    lines.extend([
        "",
        "### Improvement Suggestions",
    ])
    for imp in analysis["improvements"]:
        lines.append(f"- {imp}")
    
    lines.extend([
        "",
        "### Confidence",
        f"**{analysis['confidence']}** — *Low = minor changes, Medium = moderate risk, High = significant changes*",
        "",
        "---",
        "_🤖 Generated by claude-review agent_",
    ])
    
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="PR review agent")
    parser.add_argument("--pr", help="PR URL or number")
    parser.add_argument("--repo", help="Repository (owner/repo) — required if --pr is a number")
    args = parser.parse_args()
    
    if not args.pr:
        parser.print_help()
        sys.exit(1)
    
    # Parse PR identifier
    if args.pr.startswith("http"):
        repo, pr_number = parse_pr_url(args.pr)
    else:
        if not args.repo:
            print("Error: --repo required when --pr is a number", file=sys.stderr)
            sys.exit(1)
        repo = args.repo
        pr_number = int(args.pr)
    
    print(f"Fetching PR #{pr_number} from {repo}...", file=sys.stderr)
    pr_data = fetch_pr_data(repo, pr_number)
    print(f"Analyzing {len(pr_data.files)} files, {len(pr_data.commits)} commits...", file=sys.stderr)
    
    analysis = analyze_pr(pr_data)
    review = format_review(analysis)
    print(review)


if __name__ == "__main__":
    main()
