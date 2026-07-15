#!/usr/bin/env python3
"""
PR Reviewer Agent - Structured Markdown Output
Bounty: claude-builders-bounty/claude-builders-bounty #4
Author: FanLi (范蠡)

Reviews pull requests and generates structured Markdown reports.
Supports GitHub PRs with local git diffs.
"""

import subprocess
import re
import json
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class ReviewSeverity(str, Enum):
    CRITICAL = "🔴 CRITICAL"
    HIGH = "🟠 HIGH"
    MEDIUM = "🟡 MEDIUM"
    LOW = "🟢 LOW"
    INFO = "🔵 INFO"


class ReviewCategory(str, Enum):
    BUG = "🐛 Bug Risk"
    SECURITY = "🔒 Security"
    PERFORMANCE = "⚡ Performance"
    STYLE = "🎨 Style"
    DOCUMENTATION = "📚 Documentation"
    TESTING = "🧪 Testing"
    ARCHITECTURE = "🏗️ Architecture"


@dataclass
class ReviewFinding:
    severity: ReviewSeverity
    category: ReviewCategory
    file: str
    line: Optional[int]
    message: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None


@dataclass
class ReviewReport:
    pr_title: str
    pr_branch: str
    base_branch: str
    author: str
    findings: List[ReviewFinding] = field(default_factory=list)
    summary_stats: Dict[str, int] = field(default_factory=dict)
    review_time: str = field(default_factory=lambda: datetime.now().isoformat())


class PRReviewer:
    """PR Reviewer Agent with structured Markdown output"""

    def __init__(self):
        self.findings: List[ReviewFinding] = []

    def get_pr_info(self) -> Dict[str, str]:
        """Get current PR information from git"""
        try:
            # Try to get PR info from git
            current_branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
            # Try to get base branch (usually main or master)
            base_branch = self._detect_base_branch()
            # Get author
            author = self._run_git(["config", "user.name"])

            return {
                "title": f"Review: {current_branch}",
                "branch": current_branch,
                "base": base_branch,
                "author": author
            }
        except Exception as e:
            return {
                "title": "Local Review",
                "branch": "unknown",
                "base": "main",
                "author": "unknown"
            }

    def _detect_base_branch(self) -> str:
        """Detect the base branch (main/master)"""
        for branch in ["main", "master", "develop"]:
            try:
                self._run_git(["rev-parse", "--verify", branch])
                return branch
            except:
                continue
        return "main"

    def _run_git(self, args: List[str]) -> str:
        """Run git command and return output"""
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    def get_diff(self, base_branch: str = "main") -> str:
        """Get diff between current branch and base"""
        try:
            return self._run_git(["diff", f"{base_branch}...HEAD"])
        except:
            # Fallback to unstaged changes
            return self._run_git(["diff", "HEAD"])

    def analyze_code(self, diff: str, file_path: str) -> List[ReviewFinding]:
        """Analyze code for common issues"""
        findings = []
        lines = diff.split('\n')
        current_line = 0

        for i, line in enumerate(lines):
            # Check for added lines (start with +)
            if line.startswith('+') and not line.startswith('+++'):
                code = line[1:]  # Remove the + prefix

                # Security checks
                findings.extend(self._check_security(code, file_path, i))

                # Bug risk checks
                findings.extend(self._check_bug_risk(code, file_path, i))

                # Performance checks
                findings.extend(self._check_performance(code, file_path, i))

                # Style checks
                findings.extend(self._check_style(code, file_path, i))

        return findings

    def _check_security(self, code: str, file_path: str, line_num: int) -> List[ReviewFinding]:
        """Check for security issues"""
        findings = []

        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded token detected"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded secret detected"),
        ]

        for pattern, message in secret_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                findings.append(ReviewFinding(
                    severity=ReviewSeverity.CRITICAL,
                    category=ReviewCategory.SECURITY,
                    file=file_path,
                    line=line_num,
                    message=message,
                    suggestion="Use environment variables or a secrets manager"
                ))

        # Check for SQL injection risks
        if re.search(r'(?:execute|query|raw)\s*\(.+[%\+]', code, re.IGNORECASE):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.HIGH,
                category=ReviewCategory.SECURITY,
                file=file_path,
                line=line_num,
                message="Potential SQL injection risk",
                suggestion="Use parameterized queries instead of string concatenation"
            ))

        return findings

    def _check_bug_risk(self, code: str, file_path: str, line_num: int) -> List[ReviewFinding]:
        """Check for potential bugs"""
        findings = []

        # Check for TODO/FIXME without issue reference
        if re.search(r'#\s*(TODO|FIXME)\s*[^#]', code, re.IGNORECASE):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category=ReviewCategory.BUG,
                file=file_path,
                line=line_num,
                message="TODO/FIXME without issue reference",
                suggestion="Add issue number: TODO(#123): description"
            ))

        # Check for bare except clauses (Python)
        if re.search(r'except\s*:', code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.MEDIUM,
                category=ReviewCategory.BUG,
                file=file_path,
                line=line_num,
                message="Bare except clause catches all exceptions",
                suggestion="Use 'except SpecificException:' instead"
            ))

        # Check for undefined variables (simple check)
        if 'console.log' in code and 'debug' in code.lower():
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category=ReviewCategory.BUG,
                file=file_path,
                line=line_num,
                message="Debug logging found",
                suggestion="Remove debug logging before merging"
            ))

        return findings

    def _check_performance(self, code: str, file_path: str, line_num: int) -> List[ReviewFinding]:
        """Check for performance issues"""
        findings = []

        # Check for inefficient loops
        if re.search(r'for\s+.+in\s+range\s*\(\s*len\s*\(', code):
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category=ReviewCategory.PERFORMANCE,
                file=file_path,
                line=line_num,
                message="Using range(len()) pattern",
                suggestion="Use 'for item in iterable:' or enumerate() instead"
            ))

        return findings

    def _check_style(self, code: str, file_path: str, line_num: int) -> List[ReviewFinding]:
        """Check for style issues"""
        findings = []

        # Check for trailing whitespace
        if code.rstrip() != code:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.INFO,
                category=ReviewCategory.STYLE,
                file=file_path,
                line=line_num,
                message="Trailing whitespace detected"
            ))

        # Check for long lines
        if len(code) > 120:
            findings.append(ReviewFinding(
                severity=ReviewSeverity.LOW,
                category=ReviewCategory.STYLE,
                file=file_path,
                line=line_num,
                message=f"Line too long ({len(code)} characters)",
                suggestion="Keep lines under 120 characters"
            ))

        return findings

    def parse_diff_files(self, diff: str) -> Dict[str, str]:
        """Parse diff into individual file diffs"""
        files = {}
        current_file = None
        current_diff = []

        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                if current_file:
                    files[current_file] = '\n'.join(current_diff)
                # Extract filename from "diff --git a/path b/path"
                match = re.search(r'b/(.+)$', line)
                current_file = match.group(1) if match else line
                current_diff = [line]
            elif current_file is not None:
                current_diff.append(line)

        if current_file:
            files[current_file] = '\n'.join(current_diff)

        return files

    def review(self, base_branch: str = "main") -> ReviewReport:
        """Run full PR review"""
        # Get PR info
        pr_info = self.get_pr_info()

        # Get diff
        diff = self.get_diff(base_branch)

        if not diff:
            return ReviewReport(
                pr_title=pr_info["title"],
                pr_branch=pr_info["branch"],
                base_branch=pr_info["base"],
                author=pr_info["author"],
                findings=[],
                summary_stats={"total": 0}
            )

        # Parse files from diff
        files = self.parse_diff_files(diff)

        # Analyze each file
        all_findings = []
        for file_path, file_diff in files.items():
            findings = self.analyze_code(file_diff, file_path)
            all_findings.extend(findings)

        # Calculate stats
        stats = {
            "total": len(all_findings),
            "critical": sum(1 for f in all_findings if f.severity == ReviewSeverity.CRITICAL),
            "high": sum(1 for f in all_findings if f.severity == ReviewSeverity.HIGH),
            "medium": sum(1 for f in all_findings if f.severity == ReviewSeverity.MEDIUM),
            "low": sum(1 for f in all_findings if f.severity == ReviewSeverity.LOW),
            "info": sum(1 for f in all_findings if f.severity == ReviewSeverity.INFO),
        }

        return ReviewReport(
            pr_title=pr_info["title"],
            pr_branch=pr_info["branch"],
            base_branch=pr_info["base"],
            author=pr_info["author"],
            findings=all_findings,
            summary_stats=stats
        )

    def generate_markdown(self, report: ReviewReport) -> str:
        """Generate structured Markdown report"""
        lines = [
            "# 🔍 PR Review Report",
            "",
            f"**PR:** {report.pr_title}",
            f"**Branch:** `{report.pr_branch}` → `{report.base_branch}`",
            f"**Author:** {report.author}",
            f"**Reviewed:** {report.review_time}",
            "",
            "---",
            "",
            "## 📊 Summary",
            "",
        ]

        # Summary table
        if report.summary_stats["total"] == 0:
            lines.extend([
                "✅ **No issues found!** This PR looks good to merge.",
                "",
            ])
        else:
            lines.extend([
                "| Severity | Count |",
                "|----------|-------|",
            ])
            if report.summary_stats["critical"] > 0:
                lines.append(f"| 🔴 Critical | {report.summary_stats['critical']} |")
            if report.summary_stats["high"] > 0:
                lines.append(f"| 🟠 High | {report.summary_stats['high']} |")
            if report.summary_stats["medium"] > 0:
                lines.append(f"| 🟡 Medium | {report.summary_stats['medium']} |")
            if report.summary_stats["low"] > 0:
                lines.append(f"| 🟢 Low | {report.summary_stats['low']} |")
            if report.summary_stats["info"] > 0:
                lines.append(f"| 🔵 Info | {report.summary_stats['info']} |")
            lines.append("")

        # Findings by category
        if report.findings:
            lines.extend([
                "---",
                "",
                "## 📝 Findings",
                "",
            ])

            # Group by severity
            for severity in [ReviewSeverity.CRITICAL, ReviewSeverity.HIGH,
                            ReviewSeverity.MEDIUM, ReviewSeverity.LOW, ReviewSeverity.INFO]:
                severity_findings = [f for f in report.findings if f.severity == severity]
                if severity_findings:
                    lines.append(f"### {severity.value}")
                    lines.append("")

                    for finding in severity_findings:
                        line_info = f":{finding.line}" if finding.line else ""
                        lines.append(f"**{finding.category.value}** in `{finding.file}{line_info}`")
                        lines.append("")
                        lines.append(f"- **Issue:** {finding.message}")
                        if finding.suggestion:
                            lines.append(f"- **Suggestion:** {finding.suggestion}")
                        if finding.code_snippet:
                            lines.append("- **Code:**")
                            lines.append("  ```")
                            lines.append(f"  {finding.code_snippet}")
                            lines.append("  ```")
                        lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            "*Generated by PR Reviewer Agent*",
            f"*Bounty: claude-builders-bounty/claude-builders-bounty #4*",
        ])

        return '\n'.join(lines)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="PR Reviewer Agent")
    parser.add_argument("--base", default="main", help="Base branch to compare against")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    reviewer = PRReviewer()
    report = reviewer.review(args.base)

    if args.json:
        output = json.dumps({
            "title": report.pr_title,
            "branch": report.pr_branch,
            "base": report.base_branch,
            "author": report.author,
            "findings": [
                {
                    "severity": f.severity.value,
                    "category": f.category.value,
                    "file": f.file,
                    "line": f.line,
                    "message": f.message,
                    "suggestion": f.suggestion
                }
                for f in report.findings
            ],
            "stats": report.summary_stats
        }, indent=2)
    else:
        output = reviewer.generate_markdown(report)

    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"✅ Review saved to: {args.output}")
    else:
        print(output)

    # Exit with error code if critical issues found
    return 1 if report.summary_stats.get("critical", 0) > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
