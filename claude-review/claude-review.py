#!/usr/bin/env python3
"""
claude-review — Claude Code PR review agent

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    GITHUB_TOKEN=ghp_xxx claude-review --pr https://github.com/owner/repo/pull/123

Fetches a PR diff via GitHub API, analyzes changes, and outputs
a structured Markdown review with summary, risks, and suggestions.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int

    @classmethod
    def from_url(cls, url: str) -> "PRInfo":
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, url)
        if not match:
            raise ValueError(f"Could not parse PR URL: {url}")
        return cls(owner=match.group(1), repo=match.group(2), number=int(match.group(3)))


@dataclass
class ReviewedFile:
    path: str
    additions: int
    deletions: int
    language: str
    has_todos: bool = False
    has_fixmes: bool = False
    has_api_keys: bool = False
    has_secrets: bool = False
    risky_patterns: list = field(default_factory=list)
    summary: str = ""


@dataclass
class ReviewResult:
    pr_url: str
    pr_title: str = ""
    pr_description: str = ""
    total_additions: int = 0
    total_deletions: int = 0
    total_files: int = 0
    files: list[ReviewedFile] = field(default_factory=list)
    languages: Counter = field(default_factory=Counter)
    errors: list = field(default_factory=list)


RISKY_PATTERNS = {
    "hardcoded_secret": [
        r'(?:api[_-]?key|apikey|secret|password|passwd|token|auth)\s*[:=]\s*["\']?(?:sk[-_]|pk[-_]|test|live|prod|gh[psu]_|gho_)[A-Za-z0-9_-]{10,}',
        r'(?i)(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{6,}["\']',
    ],
    "todo_or_fixme": [
        r'(?i)(TODO|FIXME|HACK|XXX|WORKAROUND)\s*[:(-]',
    ],
    "security_concern": [
        r'(?i)(eval|exec|system|subprocess\.call|os\.system)\s*\(',
        r'raw_input\s*\(',
        r'sql_injection|SQL\s*\(.*\+\s*',
    ],
    "debug_code": [
        r'(?i)(console\.log|print|puts|echo)\s*\(?\s*["\']?(?:debug|test|testing|tmp|temp)',
        r'(?i)\.only\s*\(|\.skip\s*\(|fdescribe\s*\(|fit\s*\(',
    ],
}

EXTENSION_LANGUAGE_MAP = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript/React",
    ".jsx": "JavaScript/React",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".rb": "Ruby",
    ".php": "PHP",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".r": "R",
    ".sh": "Bash",
    ".bash": "Bash",
    ".zsh": "Bash",
    ".ps1": "PowerShell",
    ".sql": "SQL",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "Less",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".json": "JSON",
    ".xml": "XML",
    ".md": "Markdown",
    ".rst": "reStructuredText",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
    ".dockerfile": "Dockerfile",
    ".dockerignore": "Docker",
    ".env": "Environment",
    ".gitignore": "Git Config",
    ".editorconfig": "Editor Config",
}


def detect_language(filename: str) -> str:
    """Detect programming language from filename."""
    lower = filename.lower()
    if lower == "dockerfile":
        return "Dockerfile"
    for ext, lang in EXTENSION_LANGUAGE_MAP.items():
        if lower.endswith(ext):
            return lang
    # Try to detect from full filename
    filename_map = {
        "makefile": "Make",
        "gemfile": "Ruby",
        "rakefile": "Ruby",
        "vagrantfile": "Ruby",
        "compose.yaml": "Docker",
        "compose.yml": "Docker",
    }
    base = os.path.basename(lower)
    if base in filename_map:
        return filename_map[base]
    return "Unknown"


def run_gh(args: list[str], timeout: int = 30) -> Optional[str]:
    """Run gh CLI command and return stdout."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def fetch_pr_diff(pr: PRInfo) -> Optional[str]:
    """Fetch the PR diff."""
    return run_gh(["pr", "diff", str(pr.number), "--repo", f"{pr.owner}/{pr.repo}"])


def fetch_pr_info(pr: PRInfo) -> tuple[str, str]:
    """Fetch PR title and body."""
    info = run_gh([
        "pr", "view", str(pr.number),
        "--repo", f"{pr.owner}/{pr.repo}",
        "--json", "title,body",
    ])
    if info:
        try:
            data = json.loads(info)
            return data.get("title", ""), data.get("body", "")
        except json.JSONDecodeError:
            pass
    return "", ""


def analyze_diff(diff: str) -> list[ReviewedFile]:
    """Parse a unified diff and analyze each file."""
    files = []
    current_file = None
    current_additions = 0
    current_deletions = 0
    current_content = ""
    current_path = ""

    for line in diff.split("\n"):
        # New file header
        diff_start = re.match(r"^diff --git a/(.*) b/(.*)", line)
        if diff_start:
            if current_file is not None:
                files.append(current_file)
            current_path = diff_start.group(2)
            current_additions = 0
            current_deletions = 0
            current_content = ""
            current_file = None
            continue

        # Line counts
        if line.startswith("+") and not line.startswith("+++"):
            current_additions += 1
            current_content += line[1:] + "\n"
        elif line.startswith("-") and not line.startswith("---"):
            current_deletions += 1
        elif line.startswith("@@"):
            # Hunk header, skip
            continue

        # File mode changes
        if re.match(r"^(new|deleted) file", line) or re.match(r"^index ", line) or re.match(r"^--- a/", line) or re.match(r"^\+\+\+ b/", line):
            continue

        # If we hit a new file section, wrap up current
        if diff_start:
            if current_file:
                # Actually already handled above
                pass

    # Don't forget the last file
    if current_path and (current_additions > 0 or current_deletions > 0):
        lang = detect_language(current_path)
        rf = ReviewedFile(
            path=current_path,
            additions=current_additions,
            deletions=current_deletions,
            language=lang,
        )

        # Check for risky patterns in added/changed content
        for pattern_type, patterns in RISKY_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, current_content)
                if matches:
                    rf.risky_patterns.append(f"{pattern_type}: {len(matches)} match(es)")
                    if pattern_type == "hardcoded_secret":
                        rf.has_secrets = True
                    elif pattern_type == "todo_or_fixme":
                        rf.has_todos = True

        # Generate summary
        rf.summary = f"+{rf.additions}/-{rf.deletions} lines in {rf.language}"
        files.append(rf)

    return files


def generate_review(result: ReviewResult) -> str:
    """Generate structured Markdown review."""
    lines = []
    lines.append(f"# PR Review: {result.pr_title or result.pr_url}")
    lines.append("")
    lines.append(f"**PR**: {result.pr_url}")
    if result.pr_title:
        lines.append(f"**Title**: {result.pr_title}")
    lines.append(f"**Review generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    lines.append("## Summary of Changes")
    lines.append("")
    total_changes = result.total_additions + result.total_deletions
    if result.total_files == 0:
        lines.append("No file changes detected in this PR.")
    else:
        lines.append(
            f"This PR modifies **{result.total_files} file(s)** "
            f"with **+{result.total_additions}/-{result.total_deletions}** "
            f"lines of changes ({total_changes} total lines touched)."
        )
        if result.languages:
            lang_str = ", ".join(f"{lang} ({count} file(s))" for lang, count in result.languages.most_common(5))
            lines.append(f"**Languages**: {lang_str}")
    lines.append("")

    # Risks
    lines.append("## Identified Risks")
    lines.append("")
    risks_found = False
    for f in result.files:
        file_risks = []
        if f.has_secrets:
            file_risks.append("⚠️ **Possible hardcoded secret/API key** — review carefully!")
        if f.has_todos:
            file_risks.append("📝 **Contains TODO/FIXME** — consider addressing before merge")
        if f.has_api_keys:
            file_risks.append("🔑 **API key pattern detected** — ensure these are not committed")
        if f.risky_patterns:
            for p in f.risky_patterns:
                file_risks.append(f"🔍 {p}")

        if file_risks:
            risks_found = True
            lines.append(f"### `{f.path}`")
            for risk in file_risks:
                lines.append(f"- {risk}")
            lines.append("")

    if not risks_found:
        lines.append("_No significant risks detected in this diff._")
        lines.append("")

    # Improvement suggestions
    lines.append("## Improvement Suggestions")
    lines.append("")
    suggestions_found = False

    for f in result.files:
        file_suggestions = []
        if f.additions > 200:
            file_suggestions.append(f"Large file change ({f.additions} additions). Consider splitting into smaller, focused PRs for easier review.")
            suggestions_found = True
        if f.has_todos:
            file_suggestions.append("Consider filing a follow-up issue for TODOs rather than leaving them in code.")
            suggestions_found = True
        if f.language == "Unknown":
            file_suggestions.append("Unrecognized file extension — verify this file is in the correct location.")
            suggestions_found = True
        if f.additions + f.deletions > 0 and f.additions / (f.additions + f.deletions) > 0.9:
            if f.additions > 100:
                pass  # Mostly additive is normal for new features
        if f.additions > 0 and f.deletions == 0 and not f.path.startswith(".") and not f.path.startswith("test"):
            if f.path.endswith((".py", ".js", ".ts", ".go", ".rs", ".java")):
                file_suggestions.append("No tests detected in this change. Consider adding or updating tests.")
                suggestions_found = True

        if file_suggestions:
            lines.append(f"### `{f.path}`")
            for s in file_suggestions:
                lines.append(f"- 💡 {s}")
            lines.append("")

    if not suggestions_found:
        lines.append("_No specific suggestions — the change set looks clean._")
        lines.append("")

    # File breakdown
    lines.append("## Changed Files")
    lines.append("")
    lines.append("| File | Language | Changes |")
    lines.append("|------|----------|---------|")
    for f in sorted(result.files, key=lambda x: x.additions + x.deletions, reverse=True):
        changes = f"+{f.additions}/-{f.deletions}"
        lines.append(f"| `{f.path}` | {f.language} | {changes} |")
    lines.append("")

    # Confidence
    lines.append("## Review Confidence")
    lines.append("")
    if total_changes == 0:
        confidence = "Low"
        reason = "No changes detected — unable to evaluate."
    elif risks_found:
        confidence = "Medium"
        reason = "Risks identified; manual human review recommended for flagged items."
    elif total_changes > 1000:
        confidence = "Medium"
        reason = "Large diff reduces confidence in automated analysis."
    else:
        confidence = "High"
        reason = "Clean changes with clear structure and no identified risks."

    lines.append(f"**Confidence**: {confidence}")
    lines.append(f"**Reason**: {reason}")
    lines.append("")

    lines.append("---")
    lines.append(f"_Generated by claude-review · automated PR review agent_")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Claude Code PR Review Agent")
    parser.add_argument("--pr", required=True, help="PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    # Parse PR URL
    try:
        pr_info = PRInfo.from_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Fetch PR info
    title, body = fetch_pr_info(pr_info)

    # Fetch diff
    diff = fetch_pr_diff(pr_info)
    if not diff:
        print(f"Error: Could not fetch PR diff. Ensure gh CLI is installed and authenticated.", file=sys.stderr)
        sys.exit(1)

    # Analyze
    files = analyze_diff(diff)
    result = ReviewResult(
        pr_url=args.pr,
        pr_title=title,
        pr_description=body,
        total_additions=sum(f.additions for f in files),
        total_deletions=sum(f.deletions for f in files),
        total_files=len(files),
        files=files,
        languages=Counter(f.language for f in files if f.language != "Unknown"),
    )

    # Generate review
    review = generate_review(result)

    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"Review written to {args.output}")
    else:
        print(review)


if __name__ == "__main__":
    main()