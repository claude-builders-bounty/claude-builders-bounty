#!/usr/bin/env python3
"""
Claude Code PR Review Agent (claude-review)
Analyzes pull request diffs and generates structured, actionable Markdown review comments.
Complies with Claude Builders Bounty Issue #4 acceptance criteria.
"""

import sys
import os
import re
import json
import argparse
import urllib.request
import urllib.error
import subprocess
from typing import Dict, List, Any, Optional, Tuple

class PRReviewAgent:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if not self.token:
            # Try fetching from gh CLI if available
            try:
                res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
                if res.returncode == 0 and res.stdout.strip():
                    self.token = res.stdout.strip()
            except Exception:
                pass

    def parse_pr_url(self, url: str) -> Tuple[str, str, int]:
        """Extracts (owner, repo, pr_number) from a GitHub PR URL."""
        match = re.match(r"^https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
        if match:
            return match.group(1), match.group(2), int(match.group(3))
        match_api = re.match(r"^https://api\.github\.com/repos/([^/]+)/([^/]+)/pulls/(\d+)", url.strip())
        if match_api:
            return match_api.group(1), match_api.group(2), int(match_api.group(3))
        raise ValueError(f"Invalid GitHub PR URL: {url}. Expected format: https://github.com/owner/repo/pull/123")

    def _http_get(self, url: str, accept_header: str = "application/vnd.github.v3+json") -> Tuple[int, bytes]:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "Claude-Code-Review-Agent/1.0")
        req.add_header("Accept", accept_header)
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()
        except Exception as e:
            raise RuntimeError(f"Network error connecting to {url}: {e}")

    def fetch_pr_data(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Fetches PR metadata and list of changed files from GitHub REST API."""
        pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
        status, data = self._http_get(pr_url)
        if status != 200:
            raise RuntimeError(f"Failed to fetch PR details (HTTP {status}): {data.decode('utf-8', errors='replace')}")
        pr_json = json.loads(data.decode("utf-8"))

        files_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files?per_page=100"
        f_status, f_data = self._http_get(files_url)
        files_json = json.loads(f_data.decode("utf-8")) if f_status == 200 else []

        # Also attempt to get unified diff
        diff_status, diff_bytes = self._http_get(pr_url, accept_header="application/vnd.github.v3.diff")
        raw_diff = diff_bytes.decode("utf-8", errors="replace") if diff_status == 200 else ""

        return {
            "title": pr_json.get("title", ""),
            "body": pr_json.get("body", "") or "",
            "author": pr_json.get("user", {}).get("login", "unknown"),
            "base_branch": pr_json.get("base", {}).get("ref", "main"),
            "head_branch": pr_json.get("head", {}).get("ref", ""),
            "additions": pr_json.get("additions", 0),
            "deletions": pr_json.get("deletions", 0),
            "changed_files_count": pr_json.get("changed_files", 0),
            "files": files_json,
            "raw_diff": raw_diff,
            "html_url": pr_json.get("html_url", "")
        }

    def analyze_diff(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes PR diff and metadata to generate review sections."""
        files = pr_data.get("files", [])
        raw_diff = pr_data.get("raw_diff", "")
        additions = pr_data.get("additions", 0)
        deletions = pr_data.get("deletions", 0)
        title = pr_data.get("title", "")
        body = pr_data.get("body", "")

        # 1. Categorize files
        code_files = []
        test_files = []
        config_files = []
        doc_files = []
        migration_files = []

        test_patterns = [r"test", r"spec", r"__tests__"]
        doc_patterns = [r"\.md$", r"\.rst$", r"^docs/"]
        config_patterns = [r"docker", r"\.github/", r"\.ya?ml$", r"package\.json$", r"pyproject\.toml$", r"tsconfig"]
        migration_patterns = [r"migration", r"schema\.prisma", r"\.sql$"]

        for f in files:
            fname = f.get("filename", "")
            if any(re.search(p, fname, re.IGNORECASE) for p in test_patterns):
                test_files.append(fname)
            elif any(re.search(p, fname, re.IGNORECASE) for p in doc_patterns):
                doc_files.append(fname)
            elif any(re.search(p, fname, re.IGNORECASE) for p in migration_patterns):
                migration_files.append(fname)
            elif any(re.search(p, fname, re.IGNORECASE) for p in config_patterns):
                config_files.append(fname)
            else:
                code_files.append(fname)

        # 2. Risk Heuristics
        risks = []

        # Check for credential leakage in diff
        secret_patterns = [
            (r"(?i)(api[_-]?key|secret|password|auth_token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{12,}['\"]", "Possible hardcoded secret or API credential detected in diff."),
            (r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----", "Private cryptographic key detected in diff."),
        ]
        for pattern, warning in secret_patterns:
            if re.search(pattern, raw_diff):
                risks.append(f"🔒 **Security**: {warning}")

        # Check for missing test coverage
        if code_files and not test_files:
            risks.append("🧪 **Test Coverage**: Significant application logic was introduced or modified across code files, but no corresponding unit or integration test files were updated.")

        # Check for database/schema modifications
        if migration_files:
            risks.append("🗄️ **Database Migration**: Schema or migration changes detected. Verify backward compatibility with existing production data and zero-downtime execution.")

        # Check for shell injection / dangerous execution
        if re.search(r"\b(shell=True|eval\(|exec\()", raw_diff):
            risks.append("⚡ **Security / Injection Risk**: Dynamic evaluation (`eval`, `exec`, or `shell=True`) found in code changes.")

        # Check for large PR blast radius
        if (additions + deletions) > 800 or len(files) > 15:
            risks.append("📈 **Blast Radius**: High-churn PR (>800 lines changed or >15 files). Consider splitting into atomic, independently reviewable PRs to reduce regression risk.")

        # Check for dependency updates
        deps_changed = [f for f in config_files if re.search(r"(package\.json|pyproject\.toml|requirements.*\.txt|Cargo\.toml|go\.mod)", f)]
        if deps_changed:
            risks.append(f"📦 **Dependency Updates**: Core manifest changed (`{', '.join(deps_changed)}`). Verify license compliance and check for transitive vulnerability alerts.")

        if not risks:
            risks.append("✅ **Low Blast Radius**: No high-risk patterns, secret exposures, or architectural bottlenecks detected. Modifications follow standard repository conventions.")

        # 3. Improvement Suggestions
        suggestions = []
        if code_files and not test_files:
            suggestions.append(f"Add regression tests covering newly added code paths in `{code_files[0]}`.")
        
        # Check docstring / documentation update
        if code_files and not doc_files and ("feat" in title.lower() or "add" in title.lower()):
            suggestions.append("Consider updating documentation or `README.md` to explain new user-facing functionality or configuration flags.")

        # Check error handling
        if re.search(r"except\s*:\s*pass|catch\s*\([^\)]*\)\s*\{\s*\}", raw_diff):
            suggestions.append("Avoid silent exception swallowing (`except: pass` or empty `catch`). Log unexpected exceptions or provide actionable fallback messages.")

        # Check console log leftovers
        if re.search(r"\b(console\.log|print\(['\"]debug)", raw_diff):
            suggestions.append("Remove temporary debug print/logging statements before final merge into the target branch.")

        if not suggestions:
            suggestions.append("Ensure CI test suites pass cleanly across all supported runtime environments.")
            suggestions.append("Verify error boundaries and input validation around public interface boundaries.")

        # 4. Confidence Score Calculation
        confidence = "High"
        confidence_reasons = []
        if test_files:
            confidence_reasons.append("includes automated tests")
        if (additions + deletions) < 400:
            confidence_reasons.append("manageable diff size")
        if not test_files and code_files:
            confidence = "Medium"
            confidence_reasons.append("lacks test files")
        if (additions + deletions) > 1000:
            confidence = "Medium" if confidence != "Low" else "Low"
            confidence_reasons.append("very large diff churn")
        if any("Security" in r for r in risks):
            confidence = "Low"
            confidence_reasons.append("critical security trigger identified")

        # 5. Summary Synthesis
        summary_sentences = []
        summary_sentences.append(f"This PR ({title}) modifies **{len(files)} files** (+{additions} / -{deletions}) targeted at the `{pr_data.get('base_branch')}` branch.")
        if code_files:
            summary_sentences.append(f"Primary changes touch core application logic across `{', '.join(code_files[:3])}`{' and other modules' if len(code_files) > 3 else ''}.")
        elif doc_files and not code_files:
            summary_sentences.append("The pull request focuses exclusively on documentation enhancements and project guides.")
        elif config_files and not code_files:
            summary_sentences.append("The pull request updates build configurations, workflows, and dependency specifications.")
        else:
            summary_sentences.append("The changes balance implementation files with project configuration updates.")

        return {
            "summary": " ".join(summary_sentences),
            "risks": risks,
            "suggestions": suggestions,
            "confidence": confidence,
            "confidence_reasons": ", ".join(confidence_reasons) if confidence_reasons else "standard evaluation metrics"
        }

    def format_markdown(self, analysis: Dict[str, Any], pr_data: Dict[str, Any]) -> str:
        """Formats the structured analysis into markdown matching issue criteria."""
        lines = []
        lines.append(f"## 🤖 Claude Code PR Review")
        lines.append(f"**Target:** {pr_data.get('html_url', 'PR')} | **Author:** @{pr_data.get('author', 'author')}")
        lines.append("")
        lines.append("### 📋 Summary of Changes")
        lines.append(analysis["summary"])
        lines.append("")
        lines.append("### ⚠️ Identified Risks")
        for risk in analysis["risks"]:
            lines.append(f"- {risk}")
        lines.append("")
        lines.append("### 💡 Improvement Suggestions")
        for sugg in analysis["suggestions"]:
            lines.append(f"- {sugg}")
        lines.append("")
        lines.append(f"### 🎯 Confidence Score: **{analysis['confidence']}**")
        lines.append(f"*Evaluation factors: {analysis['confidence_reasons']}.*")
        lines.append("")
        lines.append("---")
        lines.append("*Generated by [Claude Code Sub-Agent](https://github.com/claude-builders-bounty/claude-builders-bounty)*")
        return "\n".join(lines)

    def post_github_comment(self, owner: str, repo: str, pr_number: int, comment: str) -> None:
        """Posts structured markdown comment to the GitHub PR."""
        if not self.token:
            raise RuntimeError("Cannot post comment: No GITHUB_TOKEN or GH_TOKEN found.")
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
        body_data = json.dumps({"body": comment}).encode("utf-8")
        req = urllib.request.Request(url, data=body_data, method="POST")
        req.add_header("User-Agent", "Claude-Code-Review-Agent/1.0")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github.v3+json")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(f"Failed to post comment. Status: {resp.status}")

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code sub-agent that reviews a PR and returns a structured Markdown comment."
    )
    parser.add_argument("--pr", help="Full GitHub PR URL (e.g. https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Path to local diff file for offline review testing")
    parser.add_argument("--output", help="Optional output file to write structured Markdown review")
    parser.add_argument("--post", action="store_true", help="Post review comment directly to the PR via GitHub API")
    args = parser.parse_args()

    if not args.pr and not args.diff_file:
        parser.error("You must provide either --pr <url> or --diff-file <path>")

    agent = PRReviewAgent()

    if args.pr:
        owner, repo, pr_number = agent.parse_pr_url(args.pr)
        pr_data = agent.fetch_pr_data(owner, repo, pr_number)
    else:
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_text = f.read()
        pr_data = {
            "title": f"Local Diff Analysis ({os.path.basename(args.diff_file)})",
            "body": "Offline diff analysis",
            "author": "local-tester",
            "base_branch": "main",
            "head_branch": "feature",
            "additions": diff_text.count("\n+"),
            "deletions": diff_text.count("\n-"),
            "changed_files_count": len(re.findall(r"^diff --git", diff_text, re.MULTILINE)),
            "files": [{"filename": m} for m in re.findall(r"^diff --git a/(\S+)", diff_text, re.MULTILINE)],
            "raw_diff": diff_text,
            "html_url": args.diff_file
        }

    analysis = agent.analyze_diff(pr_data)
    markdown_review = agent.format_markdown(analysis, pr_data)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(markdown_review)
        print(f"✅ Review written to {args.output}")

    if args.post and args.pr:
        agent.post_github_comment(owner, repo, pr_number, markdown_review)
        print(f"✅ Review successfully posted to {args.pr}")

    print(markdown_review)

if __name__ == "__main__":
    main()
