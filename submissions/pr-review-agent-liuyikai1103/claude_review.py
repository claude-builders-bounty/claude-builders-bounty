#!/usr/bin/env python3
"""
Claude PR Review Agent — CLI tool
Analyzes PR diffs and outputs structured Markdown reviews

Usage:
    python claude_review.py --pr https://github.com/owner/repo/pull/123
    python claude_review.py --pr 123 --repo owner/repo
"""

import argparse
import os
import re
import sys
from datetime import datetime


class GitHubClient:
    """GitHub API client"""

    BASE = "https://api.github.com"

    def __init__(self, token=None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def get(self, path):
        import requests
        url = f"{self.BASE}{path}"
        r = requests.get(url, headers=self.headers, timeout=30)
        if r.status_code == 200:
            return r.json()
        print(f"[warn] API {r.status_code}: {r.text[:80]}", file=sys.stderr)
        return None

    def get_pr_info(self, owner, repo, pr_number):
        return self.get(f"/repos/{owner}/{repo}/pulls/{pr_number}")

    def get_pr_files(self, owner, repo, pr_number):
        return self.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")

    def get_pr_commits(self, owner, repo, pr_number):
        return self.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/commits")

    def get_pr_diff(self, owner, repo, pr_number):
        import requests
        url = f"{self.BASE}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = {**self.headers, "Accept": "application/vnd.github.v3.diff"}
        r = requests.get(url, headers=headers, timeout=30)
        return r.text if r.status_code == 200 else None


class PRAnalyzer:
    def __init__(self, pr_info, pr_files, pr_commits, pr_diff=None, client=None):
        self.info = pr_info or {}
        self.files = pr_files or []
        self.commits = pr_commits or []
        self.diff = pr_diff or ""
        self.has_token = bool(client and client.token)

    def analyze(self):
        return {
            "summary": self._summary(),
            "risks": self._risks(),
            "suggestions": self._suggestions(),
            "stats": self._stats(),
            "confidence": self._confidence(),
        }

    def _summary(self):
        title = self.info.get("title", "Unknown")
        body = (self.info.get("body") or "")[:400]
        author = (self.info.get("user") or {}).get("login", "unknown")
        adds = sum(f.get("additions", 0) for f in self.files)
        dels = sum(f.get("deletions", 0) for f in self.files)
        return (
            f"## PR Analysis: {title}\n\n"
            f"**Author:** @{author}  \n"
            f"**Files:** {len(self.files)} ({adds:+d}/−{dels:+d} lines)  \n"
            f"**Commits:** {len(self.commits)}  \n\n"
            f"**Description:** {body[:300]}"
        )

    def _risks(self):
        risks = []
        patterns = {
            "Hardcoded credentials": [r"(?i)(password|secret|api[_-]?key|token)\s*[=:]\s*['\"](?!.*\{|env)"],
            "Debug code left": [r"(?i)(console\.log|print\(|debugger|TODO|FIXME)"],
            "No WHERE clause DELETE": [r"(?i)\bDELETE\b(?!.*(?:WHERE|LIMIT))"],
        }
        for name, pats in patterns.items():
            for p in pats:
                if re.search(p, self.diff):
                    risks.append({"type": name, "detail": f"Match: {p[:50]}..."})
                    break
        large = [f for f in self.files if f.get("changes", 0) > 500]
        if large:
            risks.append({
                "type": "Large file changes (+500 lines)",
                "detail": ", ".join(f["filename"] for f in large[:3])
            })
        return risks or [{"type": "No risks found", "detail": "Code looks clean"}]

    def _suggestions(self):
        s = []
        has_test = any("test" in f.get("filename", "").lower() for f in self.files)
        if not has_test and self.files:
            s.append("Consider adding unit tests")
        has_docs = any(f.get("filename", "").startswith("docs/") or f.get("filename", "").endswith(".md")
                      for f in self.files)
        if not has_docs and len(self.files) > 3:
            s.append("Consider updating documentation for this change")
        return s or ["Code quality looks good"]

    def _stats(self):
        return {
            "commits": len(self.commits),
            "files": len(self.files),
            "additions": sum(f.get("additions", 0) for f in self.files),
            "deletions": sum(f.get("deletions", 0) for f in self.files),
            "changes": sum(f.get("changes", 0) for f in self.files),
        }

    def _confidence(self):
        score = 0.7
        if self.files: score += 0.1
        if self.commits: score += 0.05
        if self.diff and len(self.diff) > 100: score += 0.05
        if self.has_token: score += 0.1
        return "High" if score >= 0.9 else "Medium" if score >= 0.7 else "Low"

    def format_review(self):
        r = self.analyze()
        lines = [
            r["summary"], "",
            "---",
            "## Stats",
            "",
            f"| Metric | Value |",
            "|--------|:-----:|",
            f"| Commits | {r['stats']['commits']} |",
            f"| Files | {r['stats']['files']} |",
            f"| Additions | {r['stats']['additions']:,} |",
            f"| Deletions | {r['stats']['deletions']:,} |",
            "",
            "---",
            "## Risks",
            "",
        ]
        for risk in r["risks"]:
            lines.append(f"- **{risk['type']}**: {risk['detail']}")
        lines += ["", "---", "## Suggestions", ""]
        for s in r["suggestions"]:
            lines.append(f"- {s}")
        lines += ["", "---", f"## Confidence: {r['confidence']}", "",
                   f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}_"]
        return "\n".join(lines)


def parse_pr_url(url):
    m = re.match(r"(?:https?://)?github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    return (m.group(1), m.group(2), int(m.group(3))) if m else (None, None, None)


def main():
    parser = argparse.ArgumentParser(description="PR Review Agent")
    parser.add_argument("--pr", help="PR URL")
    parser.add_argument("--owner")
    parser.add_argument("--repo")
    parser.add_argument("--number", type=int)
    parser.add_argument("--token", help="GitHub token")
    parser.add_argument("--output", "-o", help="Output file")
    args = parser.parse_args()

    owner, repo, number = None, None, None
    if args.pr:
        owner, repo, number = parse_pr_url(args.pr)
    else:
        owner, repo, number = args.owner, args.repo, args.number

    if not all([owner, repo, number]):
        print("Usage: python claude_review.py --pr https://github.com/owner/repo/pull/123", file=sys.stderr)
        sys.exit(1)

    client = GitHubClient(token=args.token)
    pr_info = client.get_pr_info(owner, repo, number)
    if not pr_info:
        print(f"Error: Cannot get PR #{number}", file=sys.stderr)
        sys.exit(1)

    pr_files = client.get_pr_files(owner, repo, number)
    pr_commits = client.get_pr_commits(owner, repo, number)
    pr_diff = client.get_pr_diff(owner, repo, number)

    analyzer = PRAnalyzer(pr_info, pr_files or [], pr_commits or [], pr_diff, client=client)
    review = analyzer.format_review()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(review)
        print(f"Review saved to: {args.output}")
    else:
        print(review)


if __name__ == "__main__":
    main()
