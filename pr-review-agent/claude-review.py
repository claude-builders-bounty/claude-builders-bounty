#!/usr/bin/env python3
"""Claude Code PR Review Agent — analyzes GitHub PRs and outputs structured Markdown reviews.

Usage:
  ./claude-review.py --pr https://github.com/owner/repo/pull/123
  ./claude-review.py --pr https://github.com/owner/repo/pull/123 --token ghp_xxxx
  ./claude-review.py --diff diff.patch
"""

import argparse
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str
    description: str
    author: str
    base_branch: str
    head_branch: str
    state: str
    created_at: str
    updated_at: str
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    commits: int = 0
    labels: list = field(default_factory=list)
    reviewers: list = field(default_factory=list)


@dataclass
class FileChange:
    filename: str
    status: str
    additions: int
    deletions: int
    patch: str = ""


@dataclass
class ReviewFinding:
    category: str  # risk | suggestion | positive
    severity: str  # high | medium | low | info
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    detail: Optional[str] = None


# ── GitHub API helpers ───────────────────────────────────────────────────────

def _api_get(url: str, token: Optional[str] = None) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"GitHub API error {e.code} for {url}: {body}", file=sys.stderr)
        raise


def _api_get_diff(url: str, token: Optional[str] = None) -> str:
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "User-Agent": "claude-review-agent/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"GitHub API error {e.code} for {url}: {body}", file=sys.stderr)
        raise


def parse_pr_url(url: str) -> tuple:
    """Parse a GitHub PR URL into (owner, repo, number)."""
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    m = re.search(pattern, url)
    if not m:
        raise ValueError(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_info(owner: str, repo: str, number: int, token: Optional[str] = None) -> PRInfo:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}"
    data = _api_get(api_url, token)

    labels = [lbl["name"] for lbl in data.get("labels", [])]
    reviewers = [r["login"] for r in data.get("requested_reviewers", [])]

    return PRInfo(
        owner=owner,
        repo=repo,
        number=number,
        title=data.get("title", ""),
        description=data.get("body", "") or "",
        author=data["user"]["login"],
        base_branch=data["base"]["label"],
        head_branch=data["head"]["label"],
        state=data.get("state", ""),
        created_at=data.get("created_at", ""),
        updated_at=data.get("updated_at", ""),
        additions=data.get("additions", 0),
        deletions=data.get("deletions", 0),
        changed_files=data.get("changed_files", 0),
        commits=data.get("commits", 0),
        labels=labels,
        reviewers=reviewers,
    )


def fetch_pr_files(owner: str, repo: str, number: int, token: Optional[str] = None) -> list[FileChange]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files"
    data = _api_get(api_url, token)
    return [
        FileChange(
            filename=f["filename"],
            status=f.get("status", "modified"),
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
            patch=f.get("patch", ""),
        )
        for f in data
    ]


def fetch_pr_commits(owner: str, repo: str, number: int, token: Optional[str] = None) -> list[dict]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/commits"
    return _api_get(api_url, token)


# ── Diff parsing ─────────────────────────────────────────────────────────────

def parse_diff(diff_text: str) -> dict[str, list[dict]]:
    """Parse unified diff into per-file hunks."""
    files = {}
    current_file = None
    current_hunk = None

    for line in diff_text.split("\n"):
        if line.startswith("--- a/"):
            continue
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            current_file = m.group(1)
            files[current_file] = []
            continue
        m = re.match(r"^@@ -(\d+),?\d* \+(\d+),?\d* @@(.+)?$", line)
        if m:
            current_hunk = {
                "old_start": int(m.group(1)),
                "new_start": int(m.group(2)),
                "section": (m.group(3) or "").strip(),
                "lines": [],
            }
            if current_file:
                files[current_file].append(current_hunk)
            continue
        if current_hunk is not None:
            current_hunk["lines"].append(line)

    return files


# ── Analysis rules ────────────────────────────────────────────────────────────

SECURITY_PATTERNS = [
    (re.compile(r"(?i)password\s*=\s*['\"][^'\"]+['\"]"), "Hardcoded password", "high"),
    (re.compile(r"(?i)(api[_-]?key|secret|token)\s*=\s*['\"][^'\"]+['\"]"), "Possible hardcoded credential", "high"),
    (re.compile(r"(?i)(?:exec|eval|os\.system|subprocess\.call|subprocess\.Popen)\("), "Code execution via shell", "high"),
    (re.compile(r"(?i)(?:SELECT|INSERT|UPDATE|DELETE)\s+.*?\bfrom\b", re.DOTALL), "SQL query in code — verify parameterization", "medium"),
    (re.compile(r"(?i)(?:innerHTML|dangerouslySetInnerHTML|v-html)"), "Potential XSS via raw HTML injection", "high"),
    (re.compile(r"(?i)allowlist|whitelist|blacklist|master|slave"), "Consider inclusive naming", "low"),
    (re.compile(r"(?i)(?:TODO|FIXME|HACK|XXX|WORKAROUND)\b"), "Unresolved TODO/FIXME", "low"),
    (re.compile(r"(?i)(?:debug|console\.log|print)\s*\(.+\)"), "Debug/logging statement may be unintentional", "info"),
    (re.compile(r"(?i)\.env(\.\w+)?$"), "Environment file — verify not committed", "high"),
    (re.compile(r"(?i)(?:sudo|chmod\s+777|chown)"), "Privilege escalation or overly permissive", "high"),
    (re.compile(r"(?i)(?:MD5|SHA1)\b"), "Weak cryptographic hash", "medium"),
    (re.compile(r"^\s*#\s*(?:pragma|noqa|type:\s*ignore)"), "Suppressed linter/type warning", "info"),
    (re.compile(r"(?i)(?:localhost|127\.0\.0\.1|0\.0\.0\.0)(?::\d+)?\s*(?!.*#\s*OK)"), "Hardcoded localhost/network address", "low"),
    (re.compile(r"(?i)(?:GRANT|ALTER\s+USER|CREATE\s+USER)"), "Database privilege statement", "medium"),
    (re.compile(r"(?i)breakpoint\(\)|import\s+pdb|ipdb\.set_trace"), "Breakpoint / debugger left in code", "high"),
]

QUALITY_PATTERNS = [
    (re.compile(r"^.{200,}$", re.MULTILINE), "Very long line (>200 chars) — consider breaking up", "low"),
    (re.compile(r"^\s*(?:if|elif|else|for|while|with)\s*\(?[^)]*\)?\s*:\s*$[\n]^\s{1,4}\S", re.MULTILINE), "Potential missing indentation", "info"),
    (re.compile(r"(?i)(?:except\s*:|except\s+Exception\s*:)"), "Bare except clause — catches all exceptions", "medium"),
    (re.compile(r"(?i)(?:type\(|isinstance)"), "Type check — consider duck typing / protocol", "info"),
    (re.compile(r"(?i)(?:pass\s*#\s*TODO|raise\s+NotImplementedError)"), "Stub / unimplemented method", "low"),
    (re.compile(r"^\s*print\s*\(", re.MULTILINE), "print() statement — consider logger", "low"),
    (re.compile(r"(?i)MAGIC_NUMBER|HARDCODED|CONSTANT"), "Magic number or hardcoded value", "low"),
    (re.compile(r"^\s*(?:var|let|const)\s+\w+\s*=\s*(?:null|undefined)\s*$", re.MULTILINE), "Unnecessary variable initialization", "info"),
    (re.compile(r"(?i)(?:any\s*:?\s*$|@ts-ignore)"), "TypeScript any / unchecked type", "low"),
]


def analyze_security(file: FileChange, findings: list[ReviewFinding]):
    for pattern, message, severity in SECURITY_PATTERNS:
        for lineno, line in enumerate(file.patch.split("\n"), 1):
            if pattern.search(line) and not line.startswith("-"):
                findings.append(ReviewFinding(
                    category="risk",
                    severity=severity,
                    message=message,
                    file=file.filename,
                    line=lineno,
                    detail=f"```\n{line.strip()[:200]}\n```",
                ))


def analyze_quality(file: FileChange, findings: list[ReviewFinding]):
    for pattern, message, severity in QUALITY_PATTERNS:
        for lineno, line in enumerate(file.patch.split("\n"), 1):
            if pattern.search(line) and not line.startswith("-"):
                findings.append(ReviewFinding(
                    category="suggestion",
                    severity=severity,
                    message=message,
                    file=file.filename,
                    line=lineno,
                ))


def analyze_dangerous_function(file: FileChange, findings: list[ReviewFinding]):
    DANGEROUS_FUNCS = {
        ".py": [
            ("pickle.load", "Unsafe deserialization (pickle)", "high"),
            ("yaml.load(", "Unsafe YAML loading (use yaml.safe_load)", "high"),
            ("eval(", "Arbitrary code execution", "high"),
            ("exec(", "Arbitrary code execution", "high"),
            ("__import__(", "Dynamic import — potential risk", "medium"),
            ("marshal.load", "Unsafe deserialization", "medium"),
            ("shelve.open", "Potentially unsafe deserialization", "medium"),
        ],
        ".js": [
            ("eval(", "Arbitrary code execution", "high"),
            ("new Function(", "Code execution via Function constructor", "high"),
            ("document.write(", "Potential XSS", "high"),
        ],
    }

    ext = Path(file.filename).suffix
    patterns = DANGEROUS_FUNCS.get(ext, [])
    for func, message, severity in patterns:
        for lineno, line in enumerate(file.patch.split("\n"), 1):
            if func in line and not line.startswith("-"):
                findings.append(ReviewFinding(
                    category="risk",
                    severity=severity,
                    message=message,
                    file=file.filename,
                    line=lineno,
                    detail=f"```\n{line.strip()[:200]}\n```",
                ))


def analyze_file_impact(files: list[FileChange], findings: list[ReviewFinding]):
    """Analyze overall file-level patterns."""
    large_files = [f for f in files if f.additions > 200]
    for f in large_files:
        findings.append(ReviewFinding(
            category="suggestion",
            severity="low",
            message=f"Large file change ({f.additions}+ lines) — consider splitting into smaller PRs",
            file=f.filename,
        ))

    deletions_only = [f for f in files if f.additions == 0 and f.deletions > 0]
    if len(deletions_only) > 5:
        findings.append(ReviewFinding(
            category="positive",
            severity="info",
            message=f"Cleanup effort: {len(deletions_only)} files are deletions-only (removing dead code)",
        ))

    config_files = [f for f in files if f.filename in (".gitignore", ".env.example", "docker-compose.yml",
                   "package.json", "requirements.txt", "go.mod")]
    if config_files:
        names = ", ".join(f.filename for f in config_files)
        findings.append(ReviewFinding(
            category="suggestion",
            severity="info",
            message=f"Configuration files changed: {names} — verify correctness",
        ))

    test_files = [f for f in files if "test" in f.filename.lower() or "spec" in f.filename.lower()]
    src_files = [f for f in files if not any(x in f.filename.lower() for x in ("test", "spec", "docs"))]
    if src_files and not test_files:
        findings.append(ReviewFinding(
            category="suggestion",
            severity="medium",
            message="Source code changes detected but no test file changes — consider adding tests",
        ))

    # Highlight binary/lock file changes
    lock_files = [f for f in files if f.filename.endswith((".lock", ".sum", ".bin")) or
                  f.filename in ("yarn.lock", "pnpm-lock.yaml", "Gemfile.lock")]
    for f in lock_files:
        if f.additions + f.deletions > 50:
            findings.append(ReviewFinding(
                category="suggestion",
                severity="info",
                message=f"Large lock file change ({f.additions}+/{f.deletions}-) — verify dependency changes",
                file=f.filename,
            ))


def analyze_diff_structure(files: list[FileChange]) -> dict:
    """Aggregate diff statistics."""
    total_additions = sum(f.additions for f in files)
    total_deletions = sum(f.deletions for f in files)

    by_extension = Counter()
    for f in files:
        ext = Path(f.filename).suffix or "(no ext)"
        by_extension[ext] += 1

    by_status = Counter(f.status for f in files)
    language_changes = {}
    for f in files:
        ext = Path(f.filename).suffix
        language_changes[ext] = language_changes.get(ext, 0) + f.additions + f.deletions

    top_languages = sorted(language_changes.items(), key=lambda x: -x[1])[:5]

    return {
        "total_additions": total_additions,
        "total_deletions": total_deletions,
        "by_extension": dict(by_extension.most_common()),
        "by_status": dict(by_status),
        "top_languages": top_languages,
    }


def analyze_commit_quality(commits: list[dict]) -> tuple[list[ReviewFinding], dict]:
    """Analyze commit messages for quality."""
    findings = []
    stats = {"total": len(commits), "meaningful": 0, "wip": 0}

    for c in commits:
        msg = c["commit"]["message"]
        first_line = msg.split("\n")[0]

        wip_patterns = ["wip", "fix me", "temp", "hack", "workaround", "asdf", "test", "debug"]
        if any(p in first_line.lower() for p in wip_patterns) or len(first_line) < 5:
            stats["wip"] += 1
        else:
            stats["meaningful"] += 1

    if stats["wip"] > stats["total"] * 0.5:
        findings.append(ReviewFinding(
            category="suggestion",
            severity="low",
            message=f"{stats['wip']}/{stats['total']} commits have WIP/unclear messages — consider squashing with meaningful messages",
        ))

    if stats["meaningful"] == stats["total"]:
        findings.append(ReviewFinding(
            category="positive",
            severity="info",
            message=f"All {stats['total']} commit(s) have meaningful messages — good practice!",
        ))

    return findings, stats


def assess_confidence(pr_info: PRInfo, findings: list[ReviewFinding], diff_stats: dict) -> str:
    """Determine confidence score: Low / Medium / High."""
    high_risk = sum(1 for f in findings if f.severity == "high")
    medium_risk = sum(1 for f in findings if f.severity == "medium" and f.category == "risk")

    if high_risk > 3:
        return "Low"
    if high_risk > 0 and medium_risk > 2:
        return "Medium"
    if pr_info.changed_files > 30:
        return "Medium"
    return "High"


# ── Output formatting ────────────────────────────────────────────────────────

def format_review(
    pr_info: PRInfo,
    findings: list[ReviewFinding],
    diff_stats: dict,
    commit_stats: dict,
    confidence: str,
) -> str:
    """Generate the structured Markdown review."""
    lines = []
    lines.append(f"# PR Review: {pr_info.title}")
    lines.append("")
    lines.append(f"> {pr_info.owner}/{pr_info.repo}#{pr_info.number}")
    lines.append("")
    lines.append(f"- **Author:** @{pr_info.author}")
    lines.append(f"- **Branch:** `{pr_info.head_branch}` → `{pr_info.base_branch}`")
    lines.append(f"- **State:** {pr_info.state}")
    lines.append(f"- **Updated:** {pr_info.updated_at}")
    lines.append(f"- **Labels:** {', '.join(pr_info.labels) if pr_info.labels else '_none_'}")
    lines.append("")

    # ── Summary ──
    lines.append("## Summary")
    lines.append("")
    summary = _generate_summary(pr_info, diff_stats, findings)
    lines.append(summary)
    lines.append("")

    lines.append("### Change Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files changed | {pr_info.changed_files} |")
    lines.append(f"| Additions | {diff_stats['total_additions']} |")
    lines.append(f"| Deletions | {diff_stats['total_deletions']} |")
    lines.append(f"| Commits | {commit_stats['total']} |")

    if diff_stats["top_languages"]:
        lang_str = ", ".join(f"{ext} ({n} lines)" for ext, n in diff_stats["top_languages"])
        lines.append(f"| Top languages | {lang_str} |")

    file_statuses = []
    for status, count in diff_stats["by_status"].items():
        file_statuses.append(f"{status}: {count}")
    if file_statuses:
        lines.append(f"| File statuses | {', '.join(file_statuses)} |")

    lines.append("")

    # ── Identified Risks ──
    risks = [f for f in findings if f.category == "risk"]
    if risks:
        lines.append("## Identified Risks")
        lines.append("")
        for r in _sort_findings(risks):
            badge = {"high": "🔴 High", "medium": "🟡 Medium", "low": "🟢 Low", "info": "ℹ️ Info"}.get(r.severity, r.severity)
            location = f"`{r.file}`" if r.file else ""
            if r.line:
                location += f":{r.line}"
            prefix = f"[{badge}]"
            if location:
                lines.append(f"- {prefix} **{r.message}** — {location}")
            else:
                lines.append(f"- {prefix} **{r.message}**")
            if r.detail:
                lines.append(f"  {r.detail}")
        lines.append("")

    # ── Improvement Suggestions ──
    suggestions = [f for f in findings if f.category == "suggestion"]
    if suggestions:
        lines.append("## Improvement Suggestions")
        lines.append("")
        for s in _sort_findings(suggestions):
            badge = {"high": "🔴", "medium": "🟡", "low": "🟢", "info": "ℹ️"}.get(s.severity, s.severity)
            location = f"`{s.file}`" if s.file else ""
            if s.line:
                location += f":{s.line}"
            if location:
                lines.append("- **" + s.message + "** (" + location + ")")
            else:
                lines.append(f"- **{s.message}**")
        lines.append("")

    # ── Positives ──
    positives = [f for f in findings if f.category == "positive"]
    if positives:
        lines.append("## What's Done Well")
        lines.append("")
        for p in positives:
            lines.append(f"- ✅ {p.message}")
        lines.append("")

    # ── Confidence ──
    lines.append("## Review Confidence")
    lines.append("")
    confidence_icon = {"Low": "🔴", "Medium": "🟡", "High": "🟢"}.get(confidence, "⚪")
    lines.append(f"{confidence_icon} **{confidence}**")
    if confidence == "Low":
        lines.append("")
        lines.append("> This review flags significant concerns. Manual review is strongly recommended.")
    elif confidence == "Medium":
        lines.append("")
        lines.append("> Some concerns were identified. Manual verification of highlighted areas is advised.")
    else:
        lines.append("")
        lines.append("> No significant issues found. Standard review practices apply.")
    lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*Review generated by claude-review agent — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    return "\n".join(lines)


def _generate_summary(pr_info: PRInfo, diff_stats: dict, findings: list[ReviewFinding]) -> str:
    """Generate a 2-3 sentence summary of the PR."""
    parts = []

    change_type = "Adds" if diff_stats["total_additions"] > diff_stats["total_deletions"] else "Removes"
    parts.append(
        f"This PR modifies **{pr_info.changed_files} files** "
        f"with **{diff_stats['total_additions']}+** and **{diff_stats['total_deletions']}-** "
        f"across **{pr_info.commits} commit(s)**."
    )

    if pr_info.description:
        desc_preview = pr_info.description.strip().split("\n")[0][:120]
        parts.append(f"**Description:** {desc_preview}")

    risk_count = sum(1 for f in findings if f.category == "risk" and f.severity in ("high", "medium"))
    suggestion_count = sum(1 for f in findings if f.category == "suggestion")
    positive_count = sum(1 for f in findings if f.category == "positive")

    parts.append(
        f"Analysis found **{risk_count} risk(s)**, "
        f"**{suggestion_count} suggestion(s)**, "
        f"and **{positive_count} positive(s)**."
    )

    return " ".join(parts)


def _sort_findings(findings: list[ReviewFinding]) -> list[ReviewFinding]:
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    return sorted(findings, key=lambda f: (severity_order.get(f.severity, 99), f.message))


# ── Main analysis ────────────────────────────────────────────────────────────

def analyze(pr_info: PRInfo, files: list[FileChange], commits: list[dict]) -> tuple[list[ReviewFinding], dict, dict]:
    """Run all analysis and return findings + stats."""
    findings = []

    # Full diff text for analysis (only from files)
    diff_text = "\n".join(
        f"--- a/{f.filename}\n+++ b/{f.filename}\n{f.patch}"
        for f in files if f.patch
    )

    for f in files:
        analyze_security(f, findings)
        analyze_quality(f, findings)
        analyze_dangerous_function(f, findings)

    analyze_file_impact(files, findings)
    diff_stats = analyze_diff_structure(files)
    commit_findings, commit_stats = analyze_commit_quality(commits)
    findings.extend(commit_findings)

    # Positive finding: clean PR
    risk_or_suggestion = sum(1 for f in findings if f.category in ("risk", "suggestion") and f.severity != "info")
    if risk_or_suggestion == 0 and pr_info.changed_files > 0:
        findings.append(ReviewFinding(
            category="positive",
            severity="info",
            message="No significant issues detected — codebase conventions are well followed",
        ))

    return findings, diff_stats, commit_stats


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — analyzes GitHub PRs and generates structured reviews.",
    )
    parser.add_argument("--pr", help="GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)")
    parser.add_argument("--diff", help="Local diff/patch file path")
    parser.add_argument("--token", help="GitHub personal access token (or GITHUB_TOKEN env)")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    args = parser.parse_args()

    if not args.pr and not args.diff:
        parser.error("Either --pr or --diff is required")

    token = args.token or os.environ.get("GITHUB_TOKEN")

    if args.pr:
        owner, repo, number = parse_pr_url(args.pr)
        print(f"Fetching PR info: {owner}/{repo}#{number} ...", file=sys.stderr)

        try:
            pr_info = fetch_pr_info(owner, repo, number, token)
            files = fetch_pr_files(owner, repo, number, token)
            commits = fetch_pr_commits(owner, repo, number, token)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"Error: PR not found or repository is private (need --token)", file=sys.stderr)
            elif e.code == 403:
                print(f"Error: API rate limit exceeded (use --token to increase limit)", file=sys.stderr)
            else:
                print(f"Error: HTTP {e.code}", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Local diff file
        diff_path = Path(args.diff)
        if not diff_path.exists():
            print(f"Error: diff file not found: {args.diff}", file=sys.stderr)
            sys.exit(1)

        diff_text = diff_path.read_text()

        # Minimal PR info for local diffs
        pr_info = PRInfo(
            owner="local",
            repo="repo",
            number=0,
            title="Local diff review",
            description="",
            author="unknown",
            base_branch="unknown",
            head_branch="unknown",
            state="draft",
            created_at="",
            updated_at="",
        )

        # Parse into files
        files = []
        parsed = parse_diff(diff_text)
        for filename, hunks in parsed.items():
            patch_lines = []
            additions = 0
            deletions = 0
            for hunk in hunks:
                for line in hunk["lines"]:
                    patch_lines.append(line)
                    if line.startswith("+"):
                        additions += 1
                    elif line.startswith("-"):
                        deletions += 1
            files.append(FileChange(
                filename=filename,
                status="modified",
                additions=additions,
                deletions=deletions,
                patch="\n".join(patch_lines),
            ))

        commits = []

    print(f"Analyzing {len(files)} file(s), {len(commits)} commit(s) ...", file=sys.stderr)
    findings, diff_stats, commit_stats = analyze(pr_info, files, commits)
    confidence = assess_confidence(pr_info, findings, diff_stats)

    print(f"Found {len(findings)} items (confidence: {confidence})", file=sys.stderr)

    review = format_review(pr_info, findings, diff_stats, commit_stats, confidence)

    if args.output:
        Path(args.output).write_text(review)
        print(f"Review written to {args.output}", file=sys.stderr)
    else:
        print(review)


if __name__ == "__main__":
    main()
