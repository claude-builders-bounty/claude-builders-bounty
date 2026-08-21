#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a PR and posts a
structured Markdown review comment.

Bounty: claude-builders-bounty #4 ($150, powered by Opire)

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --gh-token <TOKEN>

Output: structured Markdown with:
  - Summary of changes (2-3 sentences)
  - Identified risks (list)
  - Improvement suggestions (list)
  - Confidence score: Low / Medium / High

Design: pure Python 3 stdlib. Fetches the diff via the GitHub CLI (`gh`)
or the REST API. No third-party dependencies.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import Counter
from pathlib import Path

# ── Risk patterns ───────────────────────────────────────────────────────────
RISK_PATTERNS = [
    # Secrets / credentials
    (r'(?i)(api[_-]?key|secret|passw(or)?d|token|auth)\s*[:=]\s*["\'][A-Za-z0-9_\-\.]{8,}["\']', "Hardcoded secret/credential"),
    (r'AKIA[0-9A-Z]{16}', "AWS access key ID"),
    (r'ghp_[A-Za-z0-9]{20,}', "GitHub personal access token"),
    # Code injection
    (r'\beval\s*\(', "eval() — arbitrary code execution"),
    (r'\bexec\s*\(', "exec() — arbitrary code execution"),
    (r'shell\s*=\s*True', "shell=True — command injection surface"),
    (r'os\.system\s*\(', "os.system — shell invocation"),
    (r'child_process\.exec', "child_process.exec — shell invocation"),
    # SQL injection / destructive SQL
    (r'f["\'].*SELECT.*\{.*\}', "f-string in SQL query — injection risk"),
    (r'(?i)\bDROP\s+(TABLE|DATABASE)\b', "Destructive SQL: DROP"),
    (r'(?i)\bTRUNCATE\b', "Destructive SQL: TRUNCATE"),
    (r'(?i)\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "DELETE FROM without WHERE"),
    # Destructive shell
    (r'rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)', "rm -rf (recursive force delete)"),
    (r'git\s+push\b.*(--force|-f)\b', "git push --force"),
    # Path traversal
    (r'(?i)(\.\./)+', "Path traversal (../)"),
    (r'os\.path\.join\([^)]*\.\.', "Path traversal in os.path.join"),
    # Concurrency
    (r'(?i)threading\.Thread|asyncio\.create_task|go\s+func', "Concurrency introduced"),
    # Error handling
    (r'(?<!\w)except\s*:', "Bare except — swallows all errors"),
    (r'(?<!\w)except\s+Exception\s*:', "Broad except Exception"),
    # Insecure defaults
    (r'allow_all=True|require_ssl=False|verify\s*=\s*False', "Insecure option enabled"),
    (r'CORS.*\*|Access-Control-Allow-Origin:\s*\*', "CORS wide open (*)"),
]

# File extensions → language for stats
LANG = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.tsx': 'TypeScript/React',
    '.go': 'Go', '.rs': 'Rust', '.java': 'Java', '.c': 'C', '.h': 'C/C++ header',
    '.cpp': 'C++', '.sh': 'Shell', '.rb': 'Ruby', '.php': 'PHP', '.sql': 'SQL',
    '.yaml': 'YAML', '.yml': 'YAML', '.json': 'JSON', '.md': 'Markdown',
    '.html': 'HTML', '.css': 'CSS', '.vue': 'Vue', '.swift': 'Swift', '.kt': 'Kotlin',
}


def parse_pr_url(url: str) -> tuple[str, str, str]:
    """Parse a PR URL into (owner, repo, number)."""
    m = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        sys.exit(f"error: not a GitHub PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def fetch_diff(owner: str, repo: str, number: str, gh_token: str | None) -> str:
    """Fetch the PR diff via gh CLI (preferred) or REST API fallback."""
    if gh_token:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
            headers={"Authorization": f"Bearer {gh_token}",
                     "Accept": "application/vnd.github.v3.diff",
                     "User-Agent": "claude-review"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            sys.exit(f"error: API fetch failed: {e}")

    try:
        res = subprocess.run(
            ["gh", "pr", "diff", number, "--repo", f"{owner}/{repo}"],
            capture_output=True, text=True, timeout=60,
        )
        if res.returncode != 0:
            sys.exit(f"error: gh pr diff failed: {res.stderr.strip()}")
        return res.stdout
    except FileNotFoundError:
        sys.exit("error: neither --gh-token nor gh CLI available")


def split_files(diff: str) -> list[tuple[str, str]]:
    """Split unified diff into [(filename, per-file diff)]."""
    files: list[tuple[str, str]] = []
    cur_name: str | None = None
    cur_buf: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if cur_name is not None:
                files.append((cur_name, "\n".join(cur_buf)))
            m = re.search(r'diff --git a/(\S+) b/', line)
            cur_name = m.group(1) if m else line
            cur_buf = [line]
        else:
            cur_buf.append(line)
    if cur_name is not None:
        files.append((cur_name, "\n".join(cur_buf)))
    return files


def analyze_diff(diff: str) -> dict:
    """Run heuristics over the diff; return structured findings."""
    files = split_files(diff)
    stats = {
        "files": len(files),
        "additions": 0,
        "deletions": 0,
        "languages": Counter(),
        "risks": [],
        "suggestions": [],
    }
    added_lines: list[str] = []
    # Only run risk-pattern scanning on code files (not docs/markdown/config
    # where examples of dangerous commands are expected). Test files are also
    # skipped: their dangerous strings are usually fixture inputs, not real
    # executable risk.
    CODE_EXTS = {k for k, v in LANG.items() if v not in ("Markdown", "JSON", "YAML")}
    code_added: list[str] = []
    for name, fdiff in files:
        ext = Path(name).suffix.lower()
        is_test = ("test" in Path(name).stem.lower()) or ("spec" in Path(name).stem.lower())
        if ext in LANG:
            stats["languages"][LANG[ext]] += 1
        for line in fdiff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                stats["additions"] += 1
                added_lines.append(line[1:])
                if ext in CODE_EXTS and not is_test:
                    code_added.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                stats["deletions"] += 1

    in_docstring = False
    for line in code_added:
        s = line.strip()
        # Track triple-quoted docstrings across lines.
        triple = re.findall(r'"""|\'\'\'', line)
        if in_docstring:
            if triple:
                in_docstring = False
            continue
        if triple:
            # Single-line docstring or block start.
            if triple[0] in line and line.count(triple[0]) >= 2:
                in_docstring = False  # opened+closed on same line
            else:
                in_docstring = True
            continue
        # Skip comments and pattern-definition lines — not executable risk.
        if s.startswith(("#", "//", "*", "/*")):
            continue
        if "re.compile(" in line or "Pattern(" in line:
            continue
        for pattern, label in RISK_PATTERNS:
            if re.search(pattern, line):
                snippet = line.strip()[:100]
                stats["risks"].append(f"`{snippet}` — {label}")

    # Heuristic suggestions
    if stats["files"] >= 10:
        stats["suggestions"].append("Large PR (10+ files). Consider splitting into smaller reviewable changes.")
    if stats["additions"] >= 500:
        stats["suggestions"].append("Large diff (500+ added lines). Suggest prioritizing tests for the core path.")
    if not any("test" in f.lower() for f, _ in files):
        stats["suggestions"].append("No test files changed. Consider adding tests for the new behavior.")
    if stats["languages"] and len(stats["languages"]) > 2:
        stats["suggestions"].append("Multiple languages touched. Verify cross-language interface contracts.")
    if len(stats["risks"]) == 0:
        stats["suggestions"].append("No obvious risk patterns detected by heuristics. Recommend a manual review of logic and edge cases.")

    # Dedup risks while preserving order
    seen = set()
    deduped = []
    for r in stats["risks"]:
        if r not in seen:
            seen.add(r)
            deduped.append(r)
    stats["risks"] = deduped
    return stats


def confidence(stats: dict) -> str:
    """Low/Medium/High based on heuristics coverage."""
    if stats["files"] == 0:
        return "Low"
    score = 0
    if stats["additions"] <= 100:
        score += 1
    if stats["files"] <= 5:
        score += 1
    if len(stats["risks"]) == 0:
        score += 1  # no findings — confident there are no obvious issues
    if score >= 2:
        return "High"
    if score == 1:
        return "Medium"
    return "Low"


def render_markdown(owner: str, repo: str, number: str, stats: dict, conf: str) -> str:
    lang_summary = ", ".join(f"{k}×{v}" for k, v in stats["languages"].most_common(3)) or "n/a"
    summary = (
        f"This PR touches **{stats['files']} file(s)** ({stats['additions']} additions, "
        f"{stats['deletions']} deletions) in {lang_summary}."
    )
    if len(stats["risks"]) == 0:
        summary += " No obvious risk patterns were detected by the automated scan."
    else:
        summary += f" **{len(stats['risks'])} potential issue(s)** were flagged and need attention."

    risks = "\n".join(f"- {r}" for r in stats["risks"]) or "- None detected by heuristics."
    suggs = "\n".join(f"- {s}" for s in stats["suggestions"]) or "- None."

    return f"""## 🤖 Automated PR Review — #{number}

**Repository:** `{owner}/{repo}`

### Summary
{summary}

### Identified Risks
{risks}

### Improvement Suggestions
{suggs}

### Confidence Score
**{conf}** — based on diff size, scope, and heuristics coverage.

---
*Generated by [claude-review](https://github.com/chen1246/claude-builders-bounty) — heuristic-based automated review. Not a substitute for human review.*
"""


def main() -> None:
    ap = argparse.ArgumentParser(description="Review a GitHub PR and emit structured Markdown.")
    ap.add_argument("--pr", required=True, help="PR URL, e.g. https://github.com/owner/repo/pull/123")
    ap.add_argument("--gh-token", default=None, help="GitHub token (optional; falls back to gh CLI)")
    args = ap.parse_args()

    owner, repo, number = parse_pr_url(args.pr)
    diff = fetch_diff(owner, repo, number, args.gh_token or os.environ.get("GH_TOKEN"))
    stats = analyze_diff(diff)
    conf = confidence(stats)
    print(render_markdown(owner, repo, number, stats, conf))


if __name__ == "__main__":
    main()
