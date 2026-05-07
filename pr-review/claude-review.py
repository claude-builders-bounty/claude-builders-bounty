#!/usr/bin/env python3
"""
claude-review — Claude Code PR Review Agent

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo/123
  claude-review --pr 123 --repo owner/repo

Environment:
  GITHUB_TOKEN  — optional, for private repos / higher API rate limit
  CLAUDE_API_KEY — optional, enables Claude-powered deep analysis
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional


# ─── Models ──────────────────────────────────────────────────────────────────

@dataclass
class FileChange:
    path: str
    additions: int
    deletions: int
    patch: str = ""
    status: str = "modified"  # added, modified, removed, renamed


@dataclass
class PRInfo:
    owner: str
    repo: str
    number: int
    title: str = ""
    description: str = ""
    author: str = ""
    files: list[FileChange] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0


# ─── GitHub API ──────────────────────────────────────────────────────────────

def parse_pr_url(url: str) -> tuple[str, str, int]:
    """Parse PR URL or shorthand into (owner, repo, number)."""
    # Format: https://github.com/owner/repo/pull/123
    m = re.match(r'https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    # Format: owner/repo/123
    m = re.match(r'([^/]+)/([^/]+)/(\d+)', url)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise ValueError(
        f"Could not parse PR URL: {url}\n"
        "Use format: https://github.com/owner/repo/pull/123 or owner/repo/123"
    )


def github_api(path: str) -> dict | list:
    """Call GitHub REST API and return parsed JSON."""
    token = os.environ.get("GITHUB_TOKEN", "")
    url = f"https://api.github.com{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "claude-review/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code}: {e.read().decode()[:200]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_pr_info(owner: str, repo: str, number: int) -> PRInfo:
    """Fetch PR metadata and diff from GitHub."""
    pr_data = github_api(f"/repos/{owner}/{repo}/pulls/{number}")
    pr = PRInfo(owner=owner, repo=repo, number=number)
    pr.title = pr_data.get("title", "")
    pr.description = pr_data.get("body", "") or ""
    pr.author = pr_data.get("user", {}).get("login", "unknown")
    pr.additions = pr_data.get("additions", 0)
    pr.deletions = pr_data.get("deletions", 0)
    pr.changed_files = pr_data.get("changed_files", 0)

    # Fetch file list with diffs
    files_data = github_api(f"/repos/{owner}/{repo}/pulls/{number}/files?per_page=100")
    for f in files_data:
        pr.files.append(FileChange(
            path=f["filename"],
            additions=f.get("additions", 0),
            deletions=f.get("deletions", 0),
            patch=f.get("patch", ""),
            status=f.get("status", "modified"),
        ))
    return pr


# ─── Analysis Engine ─────────────────────────────────────────────────────────

@dataclass
class Risk:
    description: str
    severity: str  # high / medium / low
    file: str = ""


@dataclass
class Suggestion:
    description: str
    effort: str  # low / medium / high


@dataclass
class ReviewOutput:
    summary: str
    risks: list[Risk]
    suggestions: list[Suggestion]
    confidence: str  # Low / Medium / High
    stats: dict = field(default_factory=dict)


def analyze_pr(pr: PRInfo) -> ReviewOutput:
    """Analyze a PR and produce a structured review."""
    risks: list[Risk] = []
    suggestions: list[Suggestion] = []

    # ── Size analysis ────────────────────────────────────────────────────
    total_lines = pr.additions + pr.deletions
    large_files = [f for f in pr.files if f.additions + f.deletions > 500]

    if total_lines > 2000:
        risks.append(Risk(
            f"Very large PR ({total_lines} lines across {pr.changed_files} files). "
            f"Consider splitting into smaller, reviewable chunks.",
            "high"
        ))
    elif total_lines > 500:
        risks.append(Risk(
            f"Large PR ({total_lines} lines). Review may take longer.",
            "medium"
        ))

    if large_files:
        for f in large_files[:3]:
            risks.append(Risk(
                f"File '{f.path}' has {f.additions + f.deletions} changed lines. "
                f"Consider splitting into smaller files.",
                "medium", f.path
            ))

    # ── File type analysis ────────────────────────────────────────────────
    extensions = {}
    for f in pr.files:
        ext = os.path.splitext(f.path)[1] or "(no ext)"
        extensions[ext] = extensions.get(ext, 0) + 1

    # ── Sensitive file detection ──────────────────────────────────────────
    sensitive_patterns = [
        r"(?i)(\.env|secret|credential|password|token|key\.json|\.pem)",
        r"(?i)(db/migrate|schema\.sql)",
        r"(?i)(docker-compose|Dockerfile|kubernetes|k8s)",
        r"(?i)(Makefile|package\.json|requirements\.txt|Cargo\.toml)",
    ]

    for f in pr.files:
        for pattern in sensitive_patterns:
            if re.search(pattern, f.path):
                risks.append(Risk(
                    f"Sensitive/config file modified: '{f.path}'. "
                    f"Verify changes don't leak credentials or break the build.",
                    "high" if "env" in f.path.lower() or "secret" in f.path.lower() else "medium",
                    f.path
                ))
                break

    # ── Dependency changes ────────────────────────────────────────────────
    dep_files = {
        "package.json": "npm/node",
        "requirements.txt": "pip",
        "Cargo.toml": "cargo",
        "go.mod": "go",
        "Gemfile": "bundler",
        "Pipfile": "pipenv",
    }
    for f in pr.files:
        if f.path in dep_files or f.path.endswith("lock.json") or f.path.endswith("lock"):
            suggestions.append(Suggestion(
                f"Dependency file changed: '{f.path}'. "
                f"Run `{'npm install' if 'package' in f.path else 'pip install'}` "
                f"locally to verify the lockfile is consistent.",
                "low"
            ))

    # ── Test analysis ─────────────────────────────────────────────────────
    has_tests = any("test" in f.path.lower() or "spec" in f.path.lower() or "__test__" in f.path
                    for f in pr.files)
    if not has_tests and any(f.status == "added" for f in pr.files):
        suggestions.append(Suggestion(
            f"No test files detected in this PR. Consider adding tests for new functionality.",
            "medium"
        ))

    # ── TODO / FIXME detection ────────────────────────────────────────────
    todo_count = 0
    for f in pr.files:
        todo_count += len(re.findall(r"(?i)(TODO|FIXME|HACK|XXX|WORKAROUND)", f.patch))
    if todo_count > 0:
        suggestions.append(Suggestion(
            f"{todo_count} TODO/FIXME/HACK comments found in the diff. "
            f"Address or document before merging.",
            "low"
        ))

    # ── Generate summary ──────────────────────────────────────────────────
    added_files = [f.path for f in pr.files if f.status == "added"]
    modified_files = [f.path for f in pr.files if f.status == "modified"]
    deleted_files = [f.path for f in pr.files if f.status == "removed"]

    parts = []
    if added_files:
        parts.append(f"Adds {len(added_files)} new file(s)")
    if modified_files:
        parts.append(f"modifies {len(modified_files)} file(s)")
    if deleted_files:
        parts.append(f"removes {len(deleted_files)} file(s)")

    file_types = ", ".join(sorted(set(os.path.splitext(f)[1] for f in added_files + modified_files if os.path.splitext(f)[1])))
    type_desc = f" ({file_types})" if file_types else ""

    summary = (
        f"**{pr.title}** by @{pr.author} — "
        f"{', '.join(parts)}{type_desc}. "
        f"Total: +{pr.additions}/-{pr.deletions} lines across {pr.changed_files} files. "
        f"{'⚠️ Review carefully — large PR.' if total_lines > 500 else 'PR size is manageable.'}"
    )

    # ── Determine confidence ──────────────────────────────────────────────
    if total_lines > 2000:
        confidence = "Low"
    elif total_lines > 500:
        confidence = "Medium"
    else:
        confidence = "High"

    return ReviewOutput(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        stats={
            "total_lines": total_lines,
            "files_changed": pr.changed_files,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "extensions": extensions,
            "has_tests": has_tests,
            "todo_count": todo_count,
        }
    )


# ─── LLM Enhancement (optional) ─────────────────────────────────────────────

def enhance_with_claude(pr: PRInfo, review: ReviewOutput) -> ReviewOutput:
    """Optionally enhance the review using Claude API for deeper analysis."""
    api_key = os.environ.get("CLAUDE_API_KEY", "")
    if not api_key:
        return review

    # Build a compact diff summary for Claude
    diff_summary = []
    for f in pr.files[:5]:  # Limit to 5 files to keep prompt small
        patch_preview = f.patch[:2000] if f.patch else "(binary or large file)"
        diff_summary.append(f"### {f.path} ({f.status}, +{f.additions}/-{f.deletions})\n```diff\n{patch_preview}\n```")

    if len(pr.files) > 5:
        diff_summary.append(f"\n... and {len(pr.files) - 5} more files")

    prompt = f"""You are a senior code reviewer. Review this PR:

## PR: {pr.title}
**Author:** @{pr.author}
**Description:** {pr.description[:1000]}

## Changes: +{pr.additions}/-{pr.deletions} across {pr.changed_files} files

{chr(10).join(diff_summary)}

Provide:
1. A 2-3 sentence summary of what this PR does
2. Key risks or concerns (list)
3. Improvement suggestions (list)
4. Confidence score: Low / Medium / High

Be specific, reference file names and line numbers where relevant."""

    payload = json.dumps({
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 2000,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            text = result.get("content", [{}])[0].get("text", "")

            # Parse structured response
            if text:
                lines = text.strip().split("\n")
                summary = ""
                risks_list = []
                suggestions_list = []
                confidence = review.confidence
                section = "summary"
                for line in lines:
                    line = line.strip()
                    if line.startswith("##") or line.startswith("**"):
                        if "risk" in line.lower() or "concern" in line.lower():
                            section = "risks"
                        elif "suggestion" in line.lower() or "improvement" in line.lower():
                            section = "suggestions"
                        elif "confidence" in line.lower() or "score" in line.lower():
                            section = "confidence"
                        elif "summary" in line.lower():
                            section = "summary"
                        continue
                    if section == "summary" and line:
                        summary += " " + line
                    elif section == "risks" and line.startswith("-"):
                        text = line.lstrip("- ").strip()
                        risks_list.append(Risk(text, "medium"))
                    elif section == "suggestions" and line.startswith("-"):
                        text = line.lstrip("- ").strip()
                        suggestions_list.append(Suggestion(text, "medium"))
                    elif section == "confidence" and line:
                        for level in ["Low", "Medium", "High"]:
                            if level in line:
                                confidence = level

                return ReviewOutput(
                    summary=summary or review.summary,
                    risks=risks_list or review.risks,
                    suggestions=suggestions_list or review.suggestions,
                    confidence=confidence,
                    stats=review.stats,
                )
    except Exception as e:
        print(f"Claude enhancement unavailable (optional): {e}", file=sys.stderr)

    return review


# ─── Output Formatting ───────────────────────────────────────────────────────

def format_review(pr: PRInfo, review: ReviewOutput) -> str:
    """Format the review as structured Markdown."""
    lines = []
    lines.append(f"# PR Review: {pr.title}")
    lines.append(f"**Repository:** `{pr.owner}/{pr.repo}#{pr.number}`")
    lines.append(f"**Author:** @{pr.author}")
    lines.append(f"**Changes:** +{pr.additions}/-{pr.deletions} across {pr.changed_files} files")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary")
    lines.append(review.summary)
    lines.append("")
    lines.append("---")
    lines.append("")

    if review.risks:
        lines.append("## Identified Risks")
        lines.append("")
        for r in review.risks:
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(r.severity, "⚪")
            file_ref = f" (`{r.file}`)" if r.file else ""
            lines.append(f"- {emoji} **[{r.severity.upper()}]** {r.description}{file_ref}")
        lines.append("")
        lines.append("---")
        lines.append("")

    if review.suggestions:
        lines.append("## Improvement Suggestions")
        lines.append("")
        for s in review.suggestions:
            effort_map = {"low": "🟢", "medium": "🟡", "high": "🔴"}
            emoji = effort_map.get(s.effort, "⚪")
            lines.append(f"- {emoji} [{s.effort.upper()} effort] {s.description}")
        lines.append("")
        lines.append("---")
        lines.append("")

    lines.append("## Review Confidence")
    confidence_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}
    lines.append(f"**{confidence_emoji.get(review.confidence, '⚪')} {review.confidence}**")
    lines.append("")

    # Stats
    lines.append("### Statistics")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files changed | {review.stats.get('files_changed', 0)} |")
    lines.append(f"| Additions | {review.stats.get('additions', 0)} |")
    lines.append(f"| Deletions | {review.stats.get('deletions', 0)} |")
    lines.append(f"| Total lines changed | {review.stats.get('total_lines', 0)} |")
    lines.append(f"| Tests included | {'✅ Yes' if review.stats.get('has_tests') else '❌ No'} |")
    lines.append(f"| TODO/FIXME count | {review.stats.get('todo_count', 0)} |")
    lines.append("")

    exts = review.stats.get("extensions", {})
    if exts:
        lines.append("### File Types Changed")
        lines.append("")
        for ext, count in sorted(exts.items(), key=lambda x: -x[1]):
            lines.append(f"- `{ext}`: {count} file(s)")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) — PR #{pr.number}*")

    return "\n".join(lines)


# ─── CLI Entry Point ─────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Claude Code PR Review Agent — analyze any GitHub PR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  claude-review --pr https://github.com/owner/repo/pull/123
  claude-review --pr owner/repo/123
  claude-review --pr 123 --repo owner/repo
  claude-review --pr owner/repo/123 --output review.md
  claude-review --pr owner/repo/123 --no-claude   # Skip optional Claude enhancement
        """
    )
    parser.add_argument("--pr", required=True, help="PR URL or owner/repo/number")
    parser.add_argument("--repo", help="Repository (owner/repo), use with --pr NUMBER")
    parser.add_argument("--output", "-o", help="Write output to file instead of stdout")
    parser.add_argument("--no-claude", action="store_true", help="Skip optional Claude API enhancement")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of Markdown")

    args = parser.parse_args()

    # Parse PR identifier
    if args.repo and args.pr.isdigit():
        owner, repo = args.repo.split("/")
        number = int(args.pr)
    else:
        owner, repo, number = parse_pr_url(args.pr)

    print(f"🔍 Fetching PR {owner}/{repo}#{number}...", file=sys.stderr)
    pr = fetch_pr_info(owner, repo, number)

    print(f"📊 Analyzing {pr.changed_files} files...", file=sys.stderr)
    review = analyze_pr(pr)

    if not args.no_claude:
        print(f"🤖 Enhancing with Claude API (optional)...", file=sys.stderr)
        review = enhance_with_claude(pr, review)

    output = json.dumps({
        "summary": review.summary,
        "risks": [{"severity": r.severity, "description": r.description, "file": r.file} for r in review.risks],
        "suggestions": [{"effort": s.effort, "description": s.description} for s in review.suggestions],
        "confidence": review.confidence,
        "stats": review.stats,
    }, indent=2) if args.json else format_review(pr, review)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"✅ Written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
