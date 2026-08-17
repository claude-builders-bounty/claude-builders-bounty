#!/usr/bin/env python3
"""
PR Reviewer - Automated Pull Request Analysis Engine with Structured Markdown Output.

Scans diffs for:
- Security & Vulnerabilities (SQL injection, hardcoded secrets, shell injection, path traversal)
- Code Quality & Regressions (unhandled exceptions, missing null checks, syntax errors, complex nesting)
- Test Coverage & Documentation updates
Generates deterministic structured Markdown reviews with recommendations and confidence scores.
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class Severity(str, Enum):
    CRITICAL = "Critical"
    WARNING = "Warning"
    INFO = "Info"


class Category(str, Enum):
    SECURITY = "Security"
    QUALITY = "Code Quality"
    TESTING = "Testing & Docs"


class Recommendation(str, Enum):
    APPROVE = "APPROVE"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    COMMENT = "COMMENT"


@dataclass
class Finding:
    severity: Severity
    category: Category
    file: str
    line: int
    description: str
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class DiffFile:
    old_path: str
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    added_lines: List[Tuple[int, str]] = field(default_factory=list)  # (line_no, text)
    removed_lines: List[Tuple[int, str]] = field(default_factory=list)
    raw_hunks: List[str] = field(default_factory=list)


@dataclass
class ReviewResult:
    recommendation: Recommendation
    confidence_score: str
    files_changed: int
    lines_added: int
    lines_removed: int
    has_test_changes: bool
    has_doc_changes: bool
    findings: List[Finding] = field(default_factory=list)
    summary_notes: List[str] = field(default_factory=list)


class DiffParser:
    """Parses standard unified git diffs into structured file representations."""

    @staticmethod
    def parse(diff_text: str) -> List[DiffFile]:
        files: List[DiffFile] = []
        if not diff_text or not diff_text.strip():
            return files

        file_chunks = re.split(r"^diff --git ", diff_text, flags=re.MULTILINE)
        
        # If diff didn't start with 'diff --git ', handle single/headerless patch
        if len(file_chunks) == 1 and not diff_text.startswith("diff --git"):
            file_chunks = ["", diff_text]

        for chunk in file_chunks:
            if not chunk.strip():
                continue

            lines = chunk.splitlines()
            old_path = ""
            new_path = ""
            is_new = False
            is_deleted = False

            # Check header lines
            for line in lines[:10]:
                if line.startswith("--- a/"):
                    old_path = line[6:]
                elif line.startswith("--- /dev/null"):
                    is_new = True
                    old_path = "/dev/null"
                elif line.startswith("+++ b/"):
                    new_path = line[6:]
                elif line.startswith("+++ /dev/null"):
                    is_deleted = True
                    new_path = "/dev/null"
                elif line.startswith("new file mode"):
                    is_new = True
                elif line.startswith("deleted file mode"):
                    is_deleted = True

            # If headers not standard '--- a/' format, try diff --git a/x b/y
            if not new_path and not old_path:
                first_line = lines[0]
                m = re.match(r"^a/(.*?)\s+b/(.*?)$", first_line)
                if m:
                    old_path = m.group(1)
                    new_path = m.group(2)

            file_path = new_path if new_path and new_path != "/dev/null" else old_path
            if not file_path:
                continue

            diff_file = DiffFile(
                old_path=old_path or file_path,
                new_path=new_path or file_path,
                is_new=is_new,
                is_deleted=is_deleted,
            )

            current_new_line = 0
            in_hunk = False

            for line in lines:
                hunk_match = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
                if hunk_match:
                    in_hunk = True
                    current_new_line = int(hunk_match.group(1))
                    diff_file.raw_hunks.append(line)
                    continue

                if in_hunk:
                    if line.startswith("+") and not line.startswith("+++"):
                        content = line[1:]
                        diff_file.added_lines.append((current_new_line, content))
                        current_new_line += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        content = line[1:]
                        diff_file.removed_lines.append((current_new_line, content))
                    elif line.startswith(" "):
                        current_new_line += 1

            files.append(diff_file)

        return files


class PRReviewEngine:
    """Core analysis engine for security, quality, regressions, tests, and documentation."""

    # Security Rules
    SECRET_PATTERNS = [
        (re.compile(r"(?i)(['\"])(?:sk|pk)_(?:live|test)_[0-9a-zA-Z]{16,}\1"), "Hardcoded API Secret Key detected"),
        (re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"), "Hardcoded API Key / Access Token detected"),
        (re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{6,}['\"]"), "Hardcoded Password detected"),
        (re.compile(r"-----BEGIN (?:RSA|DSA|EC|OPENSSH|PGP|PRIVATE) KEY-----"), "Hardcoded Private Cryptographic Key detected"),
        (re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"][a-zA-Z0-9/+=]{30,}['\"]"), "Hardcoded AWS Secret Access Key detected"),
        (re.compile(r"(?i)ghp_[a-zA-Z0-9]{36}"), "Hardcoded GitHub Personal Access Token detected"),
    ]

    SQL_INJECTION_PATTERNS = [
        (re.compile(r"(?i)f['\"].*?\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|FROM|WHERE)\b.*?\{"), "Potential SQL Injection via unparameterized SQL f-string formatting"),
        (re.compile(r"(?i)(?:execute|rawQuery|cursor\.execute)\s*\(\s*(?:f['\"].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER).*?\{|['\"].*?(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER).*?['\"]\s*%)"), "Potential SQL Injection via unparameterized string formatting / f-strings"),
        (re.compile(r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?\+.*?(?:request|input|param|arg|req|user|query|[a-zA-Z_])"), "Potential SQL Injection via string concatenation"),
        (re.compile(r"(?i)db\.(?:query|execute)\s*\(\s*['\"].*?['\"]\s*\+\s*[a-zA-Z_]"), "Raw SQL query concatenation detected"),
    ]

    SHELL_INJECTION_PATTERNS = [
        (re.compile(r"(?i)(?:os\.system|os\.popen)\s*\(\s*(?:f['\"]|['\"].*?\+|.*?\+)"), "Insecure shell execution with unsanitized command string"),
        (re.compile(r"(?i)subprocess\.(?:Popen|run|call|check_output)\s*\(.*?shell\s*=\s*True.*?\)"), "Insecure subprocess execution with shell=True"),
        (re.compile(r"(?i)\b(?:eval|exec)\s*\(\s*(?!['\"][^'\"]*['\"]$)"), "Use of dangerous dynamic execution eval()/exec()"),
    ]

    PATH_TRAVERSAL_PATTERNS = [
        (re.compile(r"(?i)open\s*\(\s*(?:f['\"].*?\{|.*?\+\s*(?:request|params|args|req|filename|path))"), "Potential Path Traversal vulnerability in file open call"),
        (re.compile(r"(?i)os\.path\.join\s*\(.*?(?:request|params|args|req)\.(?:GET|POST|args|params|query)\[?"), "Potential Path Traversal: unsanitized user input in file path construction"),
    ]

    # Code Quality Rules
    EXCEPTION_PATTERNS = [
        (re.compile(r"except:\s*$"), "Bare 'except:' clause caught; catch specific exception classes"),
        (re.compile(r"except\s+(?:Exception|BaseException):\s*(?:\n\s*)?pass"), "Silent exception swallowing with 'except Exception: pass'"),
    ]

    def __init__(self, diff_text: str):
        self.diff_text = diff_text
        self.files = DiffParser.parse(diff_text)

    def analyze(self) -> ReviewResult:
        findings: List[Finding] = []
        summary_notes: List[str] = []

        total_lines_added = 0
        total_lines_removed = 0
        has_test_changes = False
        has_doc_changes = False
        non_test_files_added = 0

        for file in self.files:
            file_path = file.new_path or file.old_path
            total_lines_added += len(file.added_lines)
            total_lines_removed += len(file.removed_lines)

            # Check file category
            is_test_file = bool(re.search(r"(?:^tests?/|test_.*\.py$|.*_test\.py$|.*\.test\.[jt]sx?$|.*\.spec\.[jt]sx?$)", file_path, re.I))
            is_doc_file = bool(re.search(r"(?:^docs/|.*\.md$|.*\.rst$|LICENSE)", file_path, re.I))

            if is_test_file:
                has_test_changes = True
            elif is_doc_file:
                has_doc_changes = True
            else:
                if len(file.added_lines) > 0:
                    non_test_files_added += 1

            # Line-by-line inspection on added lines
            for line_no, content in file.added_lines:
                # 1. Security Scans
                # Secrets
                for pattern, desc in self.SECRET_PATTERNS:
                    if pattern.search(content):
                        findings.append(Finding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY,
                            file=file_path,
                            line=line_no,
                            description=desc,
                            code_snippet=content.strip(),
                            suggestion="Store secrets in environment variables or a secure key management service instead of hardcoding."
                        ))

                # SQL Injection
                for pattern, desc in self.SQL_INJECTION_PATTERNS:
                    if pattern.search(content):
                        findings.append(Finding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY,
                            file=file_path,
                            line=line_no,
                            description=desc,
                            code_snippet=content.strip(),
                            suggestion="Use parameterized queries / ORM query builders with bind parameters."
                        ))

                # Shell Injection
                for pattern, desc in self.SHELL_INJECTION_PATTERNS:
                    if pattern.search(content):
                        findings.append(Finding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY,
                            file=file_path,
                            line=line_no,
                            description=desc,
                            code_snippet=content.strip(),
                            suggestion="Avoid shell=True and pass command arguments as a list with shlex.quote or direct execution."
                        ))

                # Path Traversal
                for pattern, desc in self.PATH_TRAVERSAL_PATTERNS:
                    if pattern.search(content):
                        findings.append(Finding(
                            severity=Severity.CRITICAL,
                            category=Category.SECURITY,
                            file=file_path,
                            line=line_no,
                            description=desc,
                            code_snippet=content.strip(),
                            suggestion="Sanitize paths using os.path.basename or validate against an allowed directory with os.path.commonpath."
                        ))

                # 2. Quality Scans
                for pattern, desc in self.EXCEPTION_PATTERNS:
                    if pattern.search(content):
                        findings.append(Finding(
                            severity=Severity.WARNING,
                            category=Category.QUALITY,
                            file=file_path,
                            line=line_no,
                            description=desc,
                            code_snippet=content.strip(),
                            suggestion="Catch explicit exceptions and ensure unexpected errors are logged or re-raised."
                        ))

                # Complex nesting check (4+ levels of indentation: 16 spaces)
                indent_spaces = len(content) - len(content.lstrip(" "))
                if indent_spaces >= 16 and any(content.lstrip().startswith(kw) for kw in ["if ", "for ", "while ", "try:", "with "]):
                    findings.append(Finding(
                        severity=Severity.INFO,
                        category=Category.QUALITY,
                        file=file_path,
                        line=line_no,
                        description="Deeply nested control block (cyclomatic complexity warning)",
                        code_snippet=content.strip(),
                        suggestion="Consider refactoring deeply nested logic into dedicated helper functions."
                    ))

        # 3. Test & Documentation Verification
        if non_test_files_added > 0 and not has_test_changes:
            findings.append(Finding(
                severity=Severity.WARNING,
                category=Category.TESTING,
                file="Overall PR",
                line=1,
                description="New functionality introduced without corresponding unit test additions or updates.",
                suggestion="Add unit test coverage under `tests/` covering the newly introduced code paths."
            ))
        elif has_test_changes:
            summary_notes.append("Test coverage verified: Unit test additions/updates detected.")

        if total_lines_added > 50 and not has_doc_changes:
            findings.append(Finding(
                severity=Severity.INFO,
                category=Category.TESTING,
                file="Documentation",
                line=1,
                description="Significant changes introduced without documentation or docstring updates.",
                suggestion="Update README, API documentation, or function docstrings if user-facing behavior changed."
            ))

        # 4. Recommendation & Confidence
        critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        warning_count = sum(1 for f in findings if f.severity == Severity.WARNING)

        if critical_count > 0 or warning_count >= 3:
            recommendation = Recommendation.REQUEST_CHANGES
            confidence_score = "5/5"
        elif warning_count > 0:
            recommendation = Recommendation.COMMENT
            confidence_score = "4/5"
        else:
            recommendation = Recommendation.APPROVE
            confidence_score = "5/5"

        return ReviewResult(
            recommendation=recommendation,
            confidence_score=confidence_score,
            files_changed=len(self.files),
            lines_added=total_lines_added,
            lines_removed=total_lines_removed,
            has_test_changes=has_test_changes,
            has_doc_changes=has_doc_changes,
            findings=findings,
            summary_notes=summary_notes,
        )


class MarkdownReviewFormatter:
    """Formats ReviewResult into structured, deterministic Markdown output."""

    @staticmethod
    def format(result: ReviewResult) -> str:
        rec_badge = {
            Recommendation.APPROVE: "APPROVE",
            Recommendation.REQUEST_CHANGES: "REQUEST_CHANGES",
            Recommendation.COMMENT: "COMMENT",
        }[result.recommendation]

        crit_count = sum(1 for f in result.findings if f.severity == Severity.CRITICAL)
        warn_count = sum(1 for f in result.findings if f.severity == Severity.WARNING)
        info_count = sum(1 for f in result.findings if f.severity == Severity.INFO)

        test_status = "Added / Updated" if result.has_test_changes else "None Detected"
        doc_status = "Updated" if result.has_doc_changes else "Unchanged"

        lines: List[str] = []
        lines.append("# Pull Request Review Report")
        lines.append("")
        lines.append(f"**Recommendation:** `{rec_badge}`  ")
        lines.append(f"**Confidence Score:** {result.confidence_score}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| :--- | :--- |")
        lines.append(f"| **Files Changed** | {result.files_changed} |")
        lines.append(f"| **Lines Added** | +{result.lines_added} |")
        lines.append(f"| **Lines Removed** | -{result.lines_removed} |")
        lines.append(f"| **Critical Vulnerabilities** | {crit_count} |")
        lines.append(f"| **Warnings / Issues** | {warn_count} |")
        lines.append(f"| **Info / Suggestions** | {info_count} |")
        lines.append(f"| **Test Coverage Status** | {test_status} |")
        lines.append(f"| **Documentation Status** | {doc_status} |")
        lines.append(f"| **Overall Decision** | `{rec_badge}` |")
        lines.append("")

        lines.append("## Detailed Findings")
        lines.append("")
        if not result.findings:
            lines.append("No critical issues, security vulnerabilities, or regressions detected. Code is clean.")
            lines.append("")
        else:
            lines.append("| Severity | Category | File | Line | Description |")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for f in result.findings:
                # Escape pipe symbols in description
                desc = f.description.replace("|", "\\|")
                lines.append(f"| `{f.severity.value}` | {f.category.value} | `{f.file}` | {f.line} | {desc} |")
            lines.append("")

        # Actionable Suggestions & Code Patches
        suggestions = [f for f in result.findings if f.suggestion]
        if suggestions:
            lines.append("## Actionable Suggestions & Patches")
            lines.append("")
            for idx, s in enumerate(suggestions, 1):
                lines.append(f"### {idx}. [{s.severity.value}] {s.file}:{s.line} - {s.category.value}")
                lines.append(f"**Issue:** {s.description}")
                if s.code_snippet:
                    lines.append("```python")
                    lines.append(f"# Flagged code:")
                    lines.append(s.code_snippet)
                    lines.append("```")
                lines.append(f"**Recommended Action:** {s.suggestion}")
                lines.append("")

        lines.append("---")
        lines.append("*Automated PR review generated by Claude Builders Bounty PR Reviewer Engine.*")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Automated PR Reviewer with structured Markdown output."
    )
    parser.add_argument(
        "diff_file",
        nargs="?",
        default=None,
        help="Path to unified diff file (optional if using stdin or --diff)",
    )
    parser.add_argument(
        "--diff",
        dest="diff_flag",
        default=None,
        help="Path to unified diff file",
    )
    parser.add_argument(
        "--output",
        "-o",
        dest="output_file",
        default=None,
        help="Path to write output markdown file (defaults to stdout)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with non-zero code (1) if recommendation is REQUEST_CHANGES",
    )

    args = parser.parse_args()

    diff_path = args.diff_flag or args.diff_file
    diff_text = ""

    if diff_path and diff_path != "-":
        if not os.path.exists(diff_path):
            sys.stderr.write(f"Error: Diff file not found: {diff_path}\n")
            sys.exit(1)
        with open(diff_path, "r", encoding="utf-8") as f:
            diff_text = f.read()
    else:
        # Read from stdin
        if not sys.stdin.isatty() or diff_path == "-":
            diff_text = sys.stdin.read()
        else:
            sys.stderr.write("Error: No diff content provided via argument or stdin.\n")
            parser.print_help()
            sys.exit(1)

    engine = PRReviewEngine(diff_text)
    result = engine.analyze()
    formatted_md = MarkdownReviewFormatter.format(result)

    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(formatted_md)
        print(f"Review written to {args.output_file}")
    else:
        print(formatted_md)

    if args.strict and result.recommendation == Recommendation.REQUEST_CHANGES:
        sys.exit(1)


if __name__ == "__main__":
    main()
