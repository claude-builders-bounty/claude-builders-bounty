#!/usr/bin/env python3
"""
claude-review — AI-powered PR review agent.

CLI tool that analyses a GitHub PR diff and outputs structured Markdown review.
Uses `gh` CLI for authenticated GitHub API access.

Usage:
    python claude-review.py --pr https://github.com/owner/repo/pull/123
    python claude-review.py --pr owner/repo/123
    python claude-review.py --pr 123                          (from repo root)
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


# ── Helpers ────────────────────────────────────────────────────────────────

def run(cmd: list[str], cwd: str | None = None) -> str:
    """Run a command and return stdout, or empty string on failure."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=False, cwd=cwd, timeout=60)
        return r.stdout.decode("utf-8", errors="replace").strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, AttributeError):
        return ""


def run_gh(args: list[str], cwd: str | None = None) -> str:
    """Run gh CLI with the given args."""
    # Try common gh locations
    gh_cmd = "gh"
    for p in [r"C:\Program Files\GitHub CLI\gh.exe"]:
        if os.path.exists(p):
            gh_cmd = p
            break
    return run([gh_cmd] + args, cwd)


def parse_pr_url(pr: str) -> tuple[str, str, str]:
    """Parse PR identifier into (owner, repo, number)."""
    # https://github.com/owner/repo/pull/123
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # owner/repo/123
    m = re.match(r"([\w.-]+)/([\w.-]+)/(\d+)", pr)
    if m:
        return m.group(1), m.group(2), m.group(3)

    # 123 — try to detect from git remote
    if pr.isdigit():
        remote = run_gh(["repo", "view", "--json", "owner,name"])
        if remote:
            try:
                data = json.loads(remote)
                return data["owner"]["login"], data["name"], pr
            except (json.JSONDecodeError, KeyError, TypeError):
                pass

    raise ValueError(f"Could not parse PR identifier: {pr!r}")


def get_pr_info(owner: str, repo: str, number: str) -> dict:
    """Fetch PR metadata via gh CLI."""
    data = run_gh(["pr", "view", str(number), "--repo", f"{owner}/{repo}",
                    "--json", "title,body,author,state,headRefName,baseRefName,additions,deletions,files,createdAt,labels,mergeable,mergedBy,reviews,comments"])
    if data:
        return json.loads(data)
    return {}


def get_pr_diff(owner: str, repo: str, number: str) -> str:
    """Fetch the full PR diff."""
    return run_gh(["pr", "diff", str(number), "--repo", f"{owner}/{repo}"])


# ── Analysis ───────────────────────────────────────────────────────────────

def analyze_diff(diff: str) -> dict:
    """Analyze the PR diff and return structured results."""
    files_changed = []
    current_file = ""
    current_patch: list[str] = []
    total_additions = 0
    total_deletions = 0

    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            if current_file and current_patch:
                files_changed.append(analyze_file(current_file, "\n".join(current_patch)))
            current_file = ""
            current_patch = []
            # Extract file path from diff --git a/... b/...
            m = re.search(r" b/(.+)$", line)
            if m:
                current_file = m.group(1)
        elif line.startswith("@@ "):
            m = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))?", line)
            if m:
                added = int(m.group(2)) if m.group(2) else 1
                total_additions += added
        elif line.startswith("+") and not line.startswith("+++"):
            total_additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            total_deletions += 1

        current_patch.append(line)

    # Last file
    if current_file and current_patch:
        files_changed.append(analyze_file(current_file, "\n".join(current_patch)))

    return {
        "files": files_changed,
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "total_files": len(files_changed),
    }


def analyze_file(filepath: str, patch: str) -> dict:
    """Analyze a single file's diff."""
    ext = Path(filepath).suffix.lower()

    # Added/deleted lines
    added = len(re.findall(r"^\+(?!\+\+)", patch, re.MULTILINE))
    deleted = len(re.findall(r"^-(?!--)", patch, re.MULTILINE))

    # Language detection
    lang_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".tsx": "TypeScript (React)", ".jsx": "JavaScript (React)",
        ".go": "Go", ".rs": "Rust", ".java": "Java",
        ".rb": "Ruby", ".php": "PHP", ".cs": "C#",
        ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".sql": "SQL", ".yaml": "YAML", ".yml": "YAML",
        ".json": "JSON", ".md": "Markdown", ".html": "HTML",
        ".css": "CSS", ".scss": "SCSS",
    }
    language = ""
    for ext_key, lang in lang_map.items():
        if filepath.endswith(ext_key):
            language = lang
            break

    # Issues found in this file
    issues = find_issues(filepath, patch)

    return {
        "path": filepath,
        "language": language,
        "additions": added,
        "deletions": deleted,
        "issues": issues,
    }


SECRET_PATTERNS = [
    (r"(?i)(?:api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded API key/secret"),
    (r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]", "Hardcoded password"),
    (r"(?i)(?:token|auth_token|bearer)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded auth token"),
    (r"(?i)(?:secret|private_key|ssh_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Hardcoded secret/key"),
    (r"(?:ghp_|gho_|github_pat_)[\w-]{36,}", "GitHub token detected"),
    (r"(?:sk-[a-zA-Z0-9]{20,})", "OpenAI/Anthropic API key detected"),
]

DANGEROUS_PATTERNS = [
    (r"\beval\s*\(", "Use of eval() — security risk"),
    (r"\bexec\s*\(", "Use of exec() — code injection risk"),
    (r"\bsubprocess\.(call|Popen|run|check_output)\s*\(", "Subprocess execution — validate inputs"),
    (r"\bsqlite3\.execute\s*\(\s*f['\"]", "SQL injection risk — use parameterized queries"),
    (r"\braw\(|\.raw\s*\(", "Raw SQL — ensure parameterized"),
    (r"(?i)TODO|FIXME|HACK|XXX", "TODO/FIXME left in code"),
    (r"\bconsole\.log\b", "Console log left in production code"),
    (r"\bdebugger\b", "Debugger statement left in code"),
    (r"\bprint\s*\(", "Print/debug statement in non-trivial code"),
]


def find_issues(filepath: str, patch: str) -> list[dict]:
    """Find issues in a patch."""
    issues = []
    seen = set()

    # Only check added lines
    added_lines = re.findall(r"^\+(?!\+\+)(.*)", patch, re.MULTILINE)
    added_content = "\n".join(added_lines)

    # Check secrets
    for pattern, desc in SECRET_PATTERNS:
        for m in re.finditer(pattern, added_content):
            key = (desc, m.group(0)[:40])
            if key not in seen:
                seen.add(key)
                issues.append({
                    "type": "secret",
                    "severity": "high",
                    "message": desc,
                    "context": m.group(0)[:80],
                })

    # Check dangerous patterns
    for pattern, desc in DANGEROUS_PATTERNS:
        for m in re.finditer(pattern, added_content):
            key = (desc, m.group(0)[:40])
            if key not in seen:
                seen.add(key)
                line = get_context_line(added_lines, m.group(0))
                issues.append({
                    "type": "code_quality",
                    "severity": "medium" if "TODO" in desc or "console" in desc else "high",
                    "message": desc,
                    "context": line[:120] if line else m.group(0)[:80],
                })

    # Large file warning
    if len(patch) > 500:
        issues.append({
            "type": "size",
            "severity": "info",
            "message": f"Large diff ({len(patch)} chars) — consider splitting into smaller PRs",
            "context": "",
        })

    # Check for file pattern issues
    ext = Path(filepath).suffix.lower()
    if ext in (".py",):
        if re.search(r"^\+\s*except\s*:?\s*(#.*)?$", patch, re.MULTILINE):
            issues.append({
                "type": "code_quality",
                "severity": "medium",
                "message": "Bare except clause — catches all exceptions",
                "context": "",
            })
        if re.search(r"^\+\s*import\s+\*\s*$", patch, re.MULTILINE):
            issues.append({
                "type": "code_quality",
                "severity": "medium",
                "message": "Wildcard import (from X import *) — pollutes namespace",
                "context": "",
            })
        if re.search(r"^\+\s*pragma:\s+no-cover\b", patch, re.MULTILINE):
            issues.append({
                "type": "test",
                "severity": "info",
                "message": "# pragma: no cover — test coverage skipped",
                "context": "",
            })

    return issues


def get_context_line(lines: list[str], target: str) -> str:
    """Find the line containing target text."""
    for line in lines:
        if target in line:
            return line.strip()
    return target[:120]


def compute_confidence(analysis: dict) -> str:
    """Compute overall confidence score based on analysis depth."""
    high_issues = sum(1 for f in analysis["files"] for i in f["issues"] if i["severity"] == "high")
    total_issues = sum(len(f["issues"]) for f in analysis["files"])

    if total_issues == 0:
        return "Low"
    if high_issues > 0 or total_issues > 5:
        return "High"
    if total_issues > 2:
        return "Medium"
    return "Low"


def generate_summary(analysis: dict, pr_info: dict) -> str:
    """Generate a 2-3 sentence summary of the PR."""
    parts = []
    n_files = analysis["total_files"]
    n_add = analysis["total_additions"]
    n_del = analysis["total_deletions"]
    issues = [i for f in analysis["files"] for i in f["issues"]]

    if n_files == 1:
        file_name = analysis["files"][0]["path"]
        lang = analysis["files"][0]["language"]
        parts.append(f"This PR changes a single file (`{file_name}`)")
        if lang:
            parts[-1] += f" in {lang}"
    else:
        langs = Counter(f["language"] for f in analysis["files"] if f["language"])
        lang_str = ", ".join(f"{l} ({c})" for l, c in langs.most_common(3))
        parts.append(f"This PR modifies {n_files} files ({lang_str})")

    parts.append(f"with {n_add} additions and {n_del} deletions")

    if issues:
        sev_high = sum(1 for i in issues if i["severity"] == "high")
        sev_med = sum(1 for i in issues if i["severity"] == "medium")
        warnings = []
        if sev_high:
            warnings.append(f"{sev_high} high-severity issue{'s' if sev_high > 1 else ''}")
        if sev_med:
            warnings.append(f"{sev_med} medium-severity issue{'s' if sev_med > 1 else ''}")
        if warnings:
            parts.append(f". Analysis found {', '.join(warnings)}")

    return " ".join(parts) + "."


def generate_markdown(analysis: dict, pr_info: dict, pr_url: str) -> str:
    """Generate the full Markdown review output."""
    issues_flat = [i for f in analysis["files"] for i in f["issues"]]
    summary = generate_summary(analysis, pr_info)
    confidence = compute_confidence(analysis)

    lines = ["## PR Review Report\n"]

    # Summary
    lines.append("### Summary")
    lines.append(f"{summary}\n")

    # Overview stats
    lines.append("### Overview")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files changed | {analysis['total_files']} |")
    lines.append(f"| Additions | {analysis['total_additions']} |")
    lines.append(f"| Deletions | {analysis['total_deletions']} |")
    lines.append(f"| Issues found | {len(issues_flat)} |")
    lines.append(f"| Confidence | {confidence} |")
    lines.append("")

    # Identified Risks
    high_issues = [i for i in issues_flat if i["severity"] == "high"]
    if high_issues:
        lines.append("### Identified Risks")
        for i in high_issues:
            lines.append(f"- **{i['message']}**")
            if i.get("context"):
                lines.append(f"  ```\n  {i['context']}\n  ```")
        lines.append("")

    # Improvement Suggestions
    med_issues = [i for i in issues_flat if i["severity"] == "medium"]
    if med_issues:
        lines.append("### Improvement Suggestions")
        for i in med_issues:
            lines.append(f"- **{i['message']}**")
            if i.get("context"):
                lines.append(f"  ```\n  {i['context']}\n  ```")
        lines.append("")

    # Info items
    info_issues = [i for i in issues_flat if i["severity"] == "info"]
    if info_issues:
        lines.append("### Notes")
        for i in info_issues:
            lines.append(f"- {i['message']}")
        lines.append("")

    # Files changed breakdown
    lines.append("### Files Changed")
    lines.append("| File | Language | +/- | Issues |")
    lines.append("|------|----------|-----|--------|")
    for f in analysis["files"]:
        label = f"`{f['path']}`" if len(f['path']) < 50 else f"`...{f['path'][-47:]}`"
        lines.append(f"| {label} | {f['language']} | +{f['additions']}/-{f['deletions']} | {len(f['issues'])} |")
    lines.append("")

    # No issues case
    if not issues_flat:
        lines.append("### Assessment")
        lines.append("No issues detected in this PR. The changes look clean.\n")

    # Confidence
    lines.append("---")
    lines.append(f"*Review confidence: **{confidence}**. Generated by claude-review at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append(f"*PR: {pr_url}*")

    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PR review agent — structured Markdown review from GitHub PR diff")
    parser.add_argument("--pr", required=True, help="PR URL (https://github.com/owner/repo/pull/123) or owner/repo/123 or just number")
    parser.add_argument("--post", action="store_true", help="Post the review as a PR comment (requires gh auth)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    args = parser.parse_args()

    try:
        owner, repo, number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    repo_full = f"{owner}/{repo}"
    pr_url = f"https://github.com/{repo_full}/pull/{number}"

    print(f"🔍 Fetching PR #{number} from {repo_full}...", file=sys.stderr)

    # Get PR info
    pr_info = get_pr_info(owner, repo, number)
    if not pr_info:
        print("Error: Could not fetch PR info. Is gh CLI authenticated?", file=sys.stderr)
        sys.exit(1)

    print(f"   Title: {pr_info.get('title', 'N/A')}", file=sys.stderr)
    print(f"   Author: {pr_info.get('author', {}).get('login', 'N/A')}", file=sys.stderr)

    # Get diff
    diff = get_pr_diff(owner, repo, number)
    if not diff:
        print("Error: Could not fetch PR diff.", file=sys.stderr)
        sys.exit(1)

    print(f"   Diff size: {len(diff)} chars", file=sys.stderr)

    # Analyze
    print(f"🔬 Analysing diff...", file=sys.stderr)
    analysis = analyze_diff(diff)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    total_issues = sum(len(f["issues"]) for f in analysis["files"])

    print(f"\n📊 Results:", file=sys.stderr)
    print(f"   Files changed: {analysis['total_files']}", file=sys.stderr)
    print(f"   Lines: +{analysis['total_additions']}/-{analysis['total_deletions']}", file=sys.stderr)
    print(f"   Issues found: {total_issues}", file=sys.stderr)

    # Generate output
    markdown = generate_markdown(analysis, pr_info, pr_url)

    # Write output
    if args.output:
        with open(args.output, "w") as f:
            f.write(markdown)
        print(f"\n✅ Review written to {args.output}", file=sys.stderr)
    else:
        print("\n" + "=" * 60)
        print(markdown)

    # Post as comment
    if args.post:
        import urllib.parse
        comment_body = markdown
        # Use temp file to avoid shell escaping issues
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(comment_body)
            tmp_path = f.name
        result = run_gh(["pr", "comment", str(number), "--repo", repo_full, "--body-file", tmp_path])
        os.unlink(tmp_path)
        if result is not None:
            print(f"\n✅ Review posted as comment on PR #{number}", file=sys.stderr)
        else:
            print(f"\n⚠️  Failed to post comment", file=sys.stderr)


if __name__ == "__main__":
    main()
