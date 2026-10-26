#!/usr/bin/env python3
"""
Claude Code PR Reviewer Sub-Agent
Analyzes GitHub Pull Request diffs and outputs structured Markdown reviews.
Executable locally via CLI or inside GitHub Actions CI/CD workflows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any

# Ensure UTF-8 output across platforms
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

PR_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+)/pull/(?P<number>\d+)/?$"
)

# High-Risk Patterns for Security and Robustness Analysis
RISK_RULES = [
    {
        "name": "Unresolved TODO or FIXME Marker",
        "severity": "LOW",
        "pattern": re.compile(r"\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
        "description": "Unresolved placeholder or technical debt marker introduced in additions.",
    },
    {
        "name": "Hardcoded Secret / Token",
        "pattern": re.compile(
            r"(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA|OPENSSH|PRIVATE) KEY-----)",
            re.IGNORECASE,
        ),
        "severity": "CRITICAL",
        "description": "Potential private credential or API secret token detected in added lines.",
    },
    {
        "name": "Destructive File Operation",
        "pattern": re.compile(r"\brm\s+([^\n;|&]*\s+)?(-rf|-fr|-r\s+-f|-f\s+-r)\b", re.IGNORECASE),
        "severity": "HIGH",
        "description": "Unsafe recursive forced filesystem deletion command ('rm -rf') detected.",
    },
    {
        "name": "Unsafe Dynamic Code Execution",
        "pattern": re.compile(r"\b(eval\(|exec\(|os\.system\(|subprocess\.Popen\(.*shell\s*=\s*True)", re.IGNORECASE),
        "severity": "HIGH",
        "description": "Unsanitized dynamic code execution or shell injection vector detected.",
    },
    {
        "name": "SQL Injection Risk",
        "pattern": re.compile(
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP)\b.*(\+\s*['\"][a-zA-Z0-9_]+|%s|\$1))",
            re.IGNORECASE,
        ),
        "severity": "HIGH",
        "description": "Potential unparameterized raw SQL query string concatenation.",
    },
    {
        "name": "Unbounded Exception Catch",
        "pattern": re.compile(r"(except:\s*pass|catch\s*\([^\)]*\)\s*\{\s*\})", re.IGNORECASE),
        "severity": "MEDIUM",
        "description": "Broad exception swallowing without logging or error recovery.",
    },
]


@dataclass
class RiskItem:
    rule_name: str
    severity: str
    description: str
    line_snippet: str


@dataclass
class PRMetadata:
    owner: str
    repo: str
    number: int
    title: str
    body: str
    author: str
    base_ref: str
    head_ref: str
    additions: int
    deletions: int
    changed_files: int
    diff_text: str


class GitHubReviewer:
    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")

    def _api_request(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        method: str = "GET",
        data: bytes | None = None,
    ) -> Any:
        req_headers = {
            "User-Agent": "Claude-Code-PR-Reviewer-Agent/1.0",
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            req_headers["Authorization"] = f"Bearer {self.token}"
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw_bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    return json.loads(raw_bytes.decode("utf-8"))
                return raw_bytes.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"GitHub API Error [{err.code}] accessing {url}: {err_body}") from err

    def fetch_pr(self, pr_url: str) -> PRMetadata:
        match = PR_URL_PATTERN.match(pr_url.strip())
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: '{pr_url}'. Expected: https://github.com/owner/repo/pull/123")

        owner = match.group("owner")
        repo = match.group("repo")
        number = int(match.group("number"))

        pr_info = self._api_request(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}")
        diff_text = self._api_request(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )

        return PRMetadata(
            owner=owner,
            repo=repo,
            number=number,
            title=pr_info.get("title", ""),
            body=pr_info.get("body", "") or "",
            author=pr_info.get("user", {}).get("login", "unknown"),
            base_ref=pr_info.get("base", {}).get("ref", "main"),
            head_ref=pr_info.get("head", {}).get("ref", ""),
            additions=pr_info.get("additions", 0),
            deletions=pr_info.get("deletions", 0),
            changed_files=pr_info.get("changed_files", 0),
            diff_text=diff_text if isinstance(diff_text, str) else "",
        )

    def analyze_diff(self, diff_text: str, metadata: PRMetadata | None = None) -> dict[str, Any]:
        """Analyzes diff lines for risks, statistics, and improvement opportunities."""
        risks: list[RiskItem] = []
        suggestions: list[str] = []
        has_tests = False
        has_docs = False
        added_lines_count = 0
        deleted_lines_count = 0

        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                filepath = line[6:]
                if "test" in filepath.lower() or "spec" in filepath.lower():
                    has_tests = True
                if filepath.endswith(".md") or "doc" in filepath.lower():
                    has_docs = True
                continue

            # Only analyze added lines for introduced risks
            if line.startswith("+") and not line.startswith("+++"):
                added_lines_count += 1
                content = line[1:].strip()
                for rule in RISK_RULES:
                    if rule["pattern"].search(content):
                        risks.append(
                            RiskItem(
                                rule_name=rule["name"],
                                severity=rule["severity"],
                                description=rule["description"],
                                line_snippet=content[:90],
                            )
                        )
            elif line.startswith("-") and not line.startswith("---"):
                deleted_lines_count += 1

        has_migrations = any("migration" in line.lower() for line in diff_text.splitlines() if line.startswith("+++ b/"))
        has_dep_changes = any(f in diff_text for f in ["package.json", "requirements.txt", "Cargo.toml", "go.mod", "pom.xml"])
        has_todos = any(r.rule_name == "Unresolved TODO or FIXME Marker" for r in risks)

        # Derive actionable suggestions
        if not has_tests:
            suggestions.append("Add automated unit or integration tests verifying the newly introduced code paths.")
        if has_migrations:
            suggestions.append("Verify database migration backwards-compatibility and execute rollback dry-run.")
        if has_dep_changes:
            suggestions.append("Audit newly updated dependencies for known security vulnerabilities and lockfile consistency.")
        if has_todos:
            suggestions.append("Address or track newly introduced TODO/FIXME comments in project issue tracker.")
        if not has_docs and added_lines_count > 80:
            suggestions.append("Update relevant developer documentation or `README.md` to document new flags and options.")
        if any(r.severity == "CRITICAL" for r in risks):
            suggestions.append("Immediately revoke and rotate any detected credentials before merging into main.")
        if not suggestions:
            suggestions.append("Maintain existing automated CI/CD checks and ensure full backwards compatibility.")

        # Determine confidence score based on test coverage and risk profile
        if any(r.severity in ("CRITICAL", "HIGH") for r in risks):
            confidence = "Medium"
            conf_reason = "Elevated risk patterns detected requiring manual maintainer inspection."
        elif has_tests and added_lines_count < 500:
            confidence = "High"
            conf_reason = "Clean diff bounded in scope with dedicated test suite coverage."
        else:
            confidence = "Medium"
            conf_reason = "Standard architectural changes; verification recommended in staging environment."

        return {
            "risks": risks,
            "suggestions": suggestions,
            "confidence": confidence,
            "confidence_reason": conf_reason,
            "has_tests": has_tests,
            "has_docs": has_docs,
            "added_lines": added_lines_count,
            "deleted_lines": deleted_lines_count,
        }

    def generate_review_markdown(self, pr: PRMetadata, analysis: dict[str, Any]) -> str:
        """Constructs standardized Markdown review comment according to acceptance criteria."""
        title = pr.title
        author = pr.author
        owner = pr.owner
        repo = pr.repo
        number = pr.number

        # 2-3 sentence summary
        summary = (
            f"Pull Request [#{number}](https://github.com/{owner}/{repo}/pull/{number}) "
            f"by @{author} introduces `{title}`. "
            f"The change modifies {pr.changed_files} file(s) with +{pr.additions} additions and -{pr.deletions} deletions "
            f"targeting the `{pr.base_ref}` branch. "
            f"{'Dedicated test coverage was detected in this submission.' if analysis['has_tests'] else 'No dedicated test files were detected in the diff.'}"
        )

        # Identified Risks
        risks_md = ""
        if analysis["risks"]:
            for r in analysis["risks"]:
                risks_md += f"- **[{r.severity}] {r.rule_name}**: {r.description}\n  `Snippet:` `{r.line_snippet}`\n"
        else:
            risks_md = "- None detected. Code passed automated static safety and anti-pattern scans.\n"

        # Improvement Suggestions
        suggestions_md = ""
        for s in analysis["suggestions"]:
            suggestions_md += f"- {s}\n"

        # Confidence Score
        confidence = analysis["confidence"]
        conf_reason = analysis["confidence_reason"]

        markdown_review = f"""## 🤖 Claude Code Automated PR Review

### Summary of Changes
{summary}

### Identified Risks
{risks_md}
### Improvement Suggestions
{suggestions_md}
### Confidence Score: {confidence}
> **Rationale:** {conf_reason}

---
*Generated autonomously by Claude Code PR Reviewer Sub-Agent.*
"""
        return markdown_review

    def post_review_comment(self, owner: str, repo: str, number: int, comment_body: str) -> str:
        """Posts review comment directly to the GitHub PR."""
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{number}/comments"
        payload = json.dumps({"body": comment_body}).encode("utf-8")
        resp = self._api_request(url, method="POST", data=payload)
        return resp.get("html_url", "")


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Sub-Agent")
    parser.add_argument("--pr", type=str, help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", type=str, help="Path to local diff file")
    parser.add_argument("--output", type=str, help="Path to output markdown review file")
    parser.add_argument("--post-comment", "--comment", action="store_true", dest="post_comment", help="Post review comment directly to GitHub PR")
    parser.add_argument("--token", type=str, help="GitHub Personal Access Token")
    args = parser.parse_args()

    reviewer = GitHubReviewer(token=args.token)

    if args.pr:
        print(f"Fetching PR metadata from {args.pr}...")
        pr = reviewer.fetch_pr(args.pr)
        analysis = reviewer.analyze_diff(pr.diff_text, pr)
        review_md = reviewer.generate_review_markdown(pr, analysis)
    elif args.diff:
        diff_path = Path(args.diff)
        if not diff_path.exists():
            sys.stderr.write(f"Error: Diff file not found at {args.diff}\n")
            sys.exit(1)
        diff_text = diff_path.read_text(encoding="utf-8")
        # Dummy PR metadata for local diff
        pr = PRMetadata(
            owner="local",
            repo="local",
            number=0,
            title="Local Diff Review",
            body="Local diff inspection",
            author="local-user",
            base_ref="main",
            head_ref="local-branch",
            additions=len([l for l in diff_text.splitlines() if l.startswith("+")]),
            deletions=len([l for l in diff_text.splitlines() if l.startswith("-")]),
            changed_files=len([l for l in diff_text.splitlines() if l.startswith("+++ b/")]),
            diff_text=diff_text,
        )
        analysis = reviewer.analyze_diff(diff_text, pr)
        review_md = reviewer.generate_review_markdown(pr, analysis)
    else:
        parser.print_help()
        sys.exit(1)

    # Print review to terminal
    print("\n" + review_md)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(review_md, encoding="utf-8")
        print(f"✅ Review written to {out_path}")

    if args.post_comment and args.pr:
        print("Posting review comment to GitHub PR...")
        comment_url = reviewer.post_review_comment(pr.owner, pr.repo, pr.number, review_md)
        print(f"✅ Comment posted: {comment_url}")


if __name__ == "__main__":
    main()
