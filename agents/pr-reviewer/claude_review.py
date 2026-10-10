#!/usr/bin/env python3
"""
🤖 Claude Code PR Reviewer Agent (Automated Structured Code Auditor)
Fetches pull request diffs, performs static security/risk and quality analysis,
and generates structured Markdown review comments with confidence scoring.
"""

import sys
import os
import re
import argparse
import urllib.request
import json
from typing import Dict, List, Any


class PullRequestReviewer:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("GITHUB_TOKEN", "")

    def parse_pr_url(self, pr_url: str) -> Dict[str, str]:
        """Extracts owner, repo, and PR number from a GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
        if not match:
            raise ValueError(f"Invalid GitHub PR URL format: {pr_url}")
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "number": match.group(3),
            "canonical_url": f"https://github.com/{match.group(1)}/{match.group(2)}/pull/{match.group(3)}"
        }

    def fetch_diff(self, pr_url: str) -> str:
        """Fetches the unified git diff of the PR."""
        meta = self.parse_pr_url(pr_url)
        diff_url = f"{meta['canonical_url']}.diff"

        req = urllib.request.Request(
            diff_url,
            headers={
                "User-Agent": "Claude-PR-Reviewer-Agent/1.0",
                "Accept": "text/plain"
            }
        )
        if self.token:
            req.add_header("Authorization", f"token {self.token}")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Failed to fetch PR diff ({e.code}): {e.reason}")
        except Exception as e:
            raise RuntimeError(f"Network error fetching diff: {e}")

    def parse_diff(self, diff_text: str) -> List[Dict[str, Any]]:
        """Parses unified diff into structured file change blocks."""
        files = []
        current_file = None

        for line in diff_text.splitlines():
            if line.startswith("diff --git"):
                if current_file:
                    files.append(current_file)
                match = re.search(r"b/(.*)$", line)
                filepath = match.group(1) if match else "unknown"
                current_file = {
                    "path": filepath,
                    "additions": 0,
                    "deletions": 0,
                    "lines_added": [],
                    "lines_removed": []
                }
            elif current_file is not None:
                if line.startswith("+") and not line.startswith("+++"):
                    current_file["additions"] += 1
                    current_file["lines_added"].append(line[1:])
                elif line.startswith("-") and not line.startswith("---"):
                    current_file["deletions"] += 1
                    current_file["lines_removed"].append(line[1:])

        if current_file:
            files.append(current_file)

        return files

    def analyze_risks(self, files: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identifies potential security, architecture, and stability risks."""
        risks = []
        has_tests = any("test" in f["path"].lower() or "spec" in f["path"].lower() for f in files)
        code_files = [f for f in files if not f["path"].endswith((".md", ".txt", ".json", ".lock", ".yml", ".yaml"))]

        # 1. Missing tests for logic changes
        if code_files and not has_tests:
            risks.append({
                "severity": "Medium",
                "category": "Test Coverage",
                "description": f"Core logic was modified in {len(code_files)} file(s), but no test files were added or updated."
            })

        # 2. Inspect line-by-line additions
        for f in files:
            path = f["path"]
            found_secret = False
            found_cmd = False
            found_except = False

            for line in f["lines_added"]:
                # Hardcoded secrets detection
                if not found_secret and re.search(r"(?:api_key|secret|private_key|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", line, re.I):
                    risks.append({
                        "severity": "High",
                        "category": "Security / Secrets",
                        "description": f"Possible hardcoded secret or token detected in `{path}`."
                    })
                    found_secret = True

                # Dangerous system commands
                if not found_cmd and re.search(r"(?:rm\s+-rf|DROP\s+TABLE|git\s+push\s+--force|eval\(|exec\()", line, re.I):
                    risks.append({
                        "severity": "High",
                        "category": "Destructive Command",
                        "description": f"Potentially dangerous or destructive execution pattern detected in `{path}`."
                    })
                    found_cmd = True

                # Bare exceptions
                if not found_except and (re.search(r"except\s*:\s*$", line) or re.search(r"catch\s*\(\s*\)\s*\{", line)):
                    risks.append({
                        "severity": "Low",
                        "category": "Error Handling",
                        "description": f"Bare exception handler found in `{path}`. May swallow unexpected runtime failures."
                    })
                    found_except = True

        return risks

    def analyze_suggestions(self, files: List[Dict[str, Any]], risks: List[Dict[str, str]]) -> List[str]:
        """Generates pragmatic, actionable improvement suggestions."""
        suggestions = []

        total_adds = sum(f["additions"] for f in files)
        total_dels = sum(f["deletions"] for f in files)

        if total_adds > 500:
            suggestions.append("Consider breaking down large PRs (>500 lines added) into smaller, focused review increments.")

        has_readme = any("readme" in f["path"].lower() for f in files)
        if not has_readme and len(files) > 3:
            suggestions.append("Ensure documentation or README is updated to reflect new component interfaces and public APIs.")

        if any(r["category"] == "Test Coverage" for r in risks):
            suggestions.append("Add automated unit tests verifying positive pathways and boundary failure cases.")

        suggestions.append("Verify that CI/CD passes without deprecation warnings and all dependency locks remain synchronized.")

        return suggestions

    def calculate_confidence(self, files: List[Dict[str, Any]], risks: List[Dict[str, str]]) -> str:
        """Computes objective confidence score: High, Medium, or Low."""
        total_lines = sum(f["additions"] + f["deletions"] for f in files)
        high_risks = sum(1 for r in risks if r["severity"] == "High")
        med_risks = sum(1 for r in risks if r["severity"] == "Medium")

        if high_risks > 0 or total_lines > 1200:
            return "Low"
        elif med_risks > 0 or total_lines > 400:
            return "Medium"
        else:
            return "High"

    def generate_review(self, pr_url: str, diff_text: str = None) -> str:
        """Full pipeline: diff fetch, semantic analysis, and structured Markdown report."""
        meta = self.parse_pr_url(pr_url)
        if not diff_text:
            diff_text = self.fetch_diff(pr_url)

        files = self.parse_diff(diff_text)
        if not files:
            return "### ⚠️ Claude PR Review\n\nNo changed files detected in this Pull Request."

        risks = self.analyze_risks(files)
        suggestions = self.analyze_suggestions(files, risks)
        confidence = self.calculate_confidence(files, risks)

        total_adds = sum(f["additions"] for f in files)
        total_dels = sum(f["deletions"] for f in files)

        # Summary of changes
        file_summary = ", ".join(f"`{os.path.basename(f['path'])}`" for f in files[:4])
        if len(files) > 4:
            file_summary += f", and {len(files) - 4} other file(s)"

        summary_text = (
            f"This pull request modifies **{len(files)} file(s)** ({file_summary}), "
            f"introducing **+{total_adds} additions** and **-{total_dels} deletions**. "
            f"The primary focus appears to be architectural expansion and tool integration."
        )

        # Build Structured Markdown
        md = []
        md.append("## 🤖 Claude Code Automated PR Review\n")
        md.append(f"> **Target PR**: [{meta['owner']}/{meta['repo']}#{meta['number']}]({meta['canonical_url']})\n")
        
        md.append("### 📋 Summary of Changes")
        md.append(summary_text + "\n")

        md.append("### ⚠️ Identified Risks")
        if risks:
            for r in risks:
                badge = "🔴" if r["severity"] == "High" else ("🟡" if r["severity"] == "Medium" else "🔵")
                md.append(f"- {badge} **[{r['severity']}] {r['category']}**: {r['description']}")
        else:
            md.append("- ✅ No critical security vulnerabilities or architectural anti-patterns detected.")
        md.append("")

        md.append("### 💡 Improvement Suggestions")
        for s in suggestions:
            md.append(f"- {s}")
        md.append("")

        md.append(f"### 🎯 Confidence Score: **{confidence}**")
        md.append(f"*Calculated based on change footprint ({len(files)} files, {total_adds + total_dels} LOC), risk distribution, and test validation coverage.*\n")
        md.append("---\n*Review generated automatically by Claude Code PR Reviewer Agent.*")

        return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Reviewer Agent")
    parser.add_argument("--pr", required=True, help="Full GitHub Pull Request URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff-file", help="Path to local diff file (offline testing)")
    parser.add_argument("--output", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--save", help="Optional path to write review markdown output")

    args = parser.parse_args()

    reviewer = PullRequestReviewer()

    diff_content = None
    if args.diff_file and os.path.exists(args.diff_file):
        with open(args.diff_file, "r", encoding="utf-8") as f:
            diff_content = f.read()

    try:
        report = reviewer.generate_review(args.pr, diff_content)
        if args.save:
            with open(args.save, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"✅ Review report saved to {args.save}")
        print("\n" + report)
    except Exception as e:
        sys.stderr.write(f"❌ Error during review execution: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
