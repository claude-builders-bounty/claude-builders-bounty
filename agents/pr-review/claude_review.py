#!/usr/bin/env python3
"""claude-review — structured Markdown review of a GitHub pull request.

Usage:
  python3 claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 claude_review.py --repo owner/repo --pr-number 123

Requires GitHub CLI (`gh`) authenticated for private repos; public works anonymously
if you set GH_TOKEN or use `gh` auth.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RISK_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"eval\s*\(|exec\s*\(|pickle\.loads|subprocess\.(?:call|run|Popen)\([^)]*shell\s*=\s*True", re.I),
     "Possible code execution / shell=True"),
    (re.compile(r"(?:password|secret|api[_-]?key|token|private[_-]?key)\s*[=:]\s*['\"][^'\"]{8,}", re.I),
     "Hardcoded credential-like string"),
    (re.compile(r"SELECT\s+\*|DELETE\s+FROM\s+\w+\s*(?:;|$)", re.I),
     "SQL: SELECT * or DELETE without WHERE"),
    (re.compile(r"innerHTML\s*=|dangerouslySetInnerHTML", re.I),
     "Raw HTML injection surface"),
    (re.compile(r"catch\s*(?:\([^)]*\))?\s*\{\s*\}|except\s*:\s*pass", re.I),
     "Swallowed exception"),
    (re.compile(r"TODO|FIXME|XXX|HACK", re.I),
     "TODO/FIXME left in diff"),
    (re.compile(r"console\.log\s*\(", re.I),
     "console.log in shipped code"),
    (re.compile(r"rm\s+-rf|force\s*push|--hard", re.I),
     "Destructive command in diff"),
]


@dataclass
class Review:
    pr_url: str
    title: str
    author: str
    files_changed: int
    additions: int
    deletions: int
    summary: str = ""
    risks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "Medium"


def gh_json(args: list[str]) -> dict | list | None:
    env = os.environ.copy()
    result = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8", env=env)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        return None
    text = result.stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def parse_pr_url(url: str) -> tuple[str, int] | None:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2)}", int(m.group(3))


def fetch_pr(repo: str, number: int) -> tuple[dict, str]:
    meta = gh_json(["api", f"repos/{repo}/pulls/{number}"])
    diff = subprocess.run(
        ["gh", "api", f"repos/{repo}/pulls/{number}", "-H", "Accept: application/vnd.github.v3.diff"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if diff.returncode != 0:
        print(diff.stderr, file=sys.stderr)
    return meta or {}, diff.stdout or ""


def scan_diff(diff: str) -> list[str]:
    hits: list[str] = []
    for pattern, label in RISK_PATTERNS:
        if pattern.search(diff):
            hits.append(label)
    # unique preserve order
    seen: set[str] = set()
    out: list[str] = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            out.append(h)
    return out


def build_summary(meta: dict, diff: str) -> str:
    title = meta.get("title") or "pull request"
    body = (meta.get("body") or "").strip().splitlines()
    first_body = next((ln.strip() for ln in body if ln.strip() and not ln.strip().startswith("#")), "")
    files = meta.get("changed_files") or 0
    adds = meta.get("additions") or 0
    dels = meta.get("deletions") or 0
    parts = [
        f'This PR titled "{title}" changes {files} file(s) (+{adds}/-{dels}).',
    ]
    if first_body:
        parts.append(f"Author states: {first_body[:180]}")
    else:
        parts.append("No PR description provided.")
    # rough intent from paths
    paths = re.findall(r"^\+\+\+ b/(.+)$", diff, re.M)
    if paths:
        top = ", ".join(paths[:4])
        parts.append(f"Touched paths include: {top}.")
    return " ".join(parts)


def build_suggestions(risks: list[str], diff: str) -> list[str]:
    sugs: list[str] = []
    if any("credential" in r.lower() or "secret" in r.lower() for r in risks):
        sugs.append("Move secrets to environment variables and rotate any exposed value.")
    if any("SQL" in r for r in risks):
        sugs.append("Prefer parameterized queries and add a WHERE clause to DELETE.")
    if any("innerHTML" in r or "HTML injection" in r for r in risks):
        sugs.append("Use textContent or a sanitizer library instead of raw HTML.")
    if any("Swallowed" in r for r in risks):
        sugs.append("Log or rethrow errors; empty catch hides production failures.")
    if any("console.log" in r for r in risks):
        sugs.append("Remove debug logging or route it through a leveled logger.")
    if any("TODO" in r for r in risks):
        sugs.append("Resolve TODO/FIXME or convert to a tracked issue before merge.")
    if "test" not in diff.lower() and re.search(r"^\+\+\+ b/.*\.(ts|tsx|js|py|go|rs)$", diff, re.M):
        sugs.append("Add or update unit tests covering the changed behavior.")
    if not sugs:
        sugs.append("No high-signal issues from static scan; consider a focused manual review of edge cases.")
    return sugs


def confidence_for(meta: dict, risks: list[str], diff: str) -> str:
    files = meta.get("changed_files") or 0
    adds = meta.get("additions") or 0
    has_tests = bool(re.search(r"test|spec", diff, re.I))
    if files <= 5 and adds < 200 and (has_tests or not risks):
        return "High"
    if files > 25 or adds > 2000 or len(risks) >= 4:
        return "Low"
    return "Medium"


def render(review: Review) -> str:
    lines = [
        f"# PR Review: {review.title}",
        "",
        f"- **URL:** {review.pr_url}",
        f"- **Author:** @{review.author}",
        f"- **Files:** {review.files_changed} (+{review.additions}/-{review.deletions})",
        "",
        "## Summary of changes",
        "",
        review.summary,
        "",
        "## Identified risks",
        "",
    ]
    if review.risks:
        lines += [f"- {r}" for r in review.risks]
    else:
        lines.append("- None detected by static scan.")
    lines += ["", "## Improvement suggestions", ""]
    lines += [f"- {s}" for s in review.suggestions]
    lines += [
        "",
        "## Confidence score",
        "",
        f"**{review.confidence}**",
        "",
        "---",
        "_Generated by claude-review (static scan + PR metadata). Not a security audit._",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Structured Markdown review of a GitHub PR")
    ap.add_argument("--pr", help="Full PR URL")
    ap.add_argument("--repo", help="owner/repo (with --pr-number)")
    ap.add_argument("--pr-number", type=int, help="PR number")
    ap.add_argument("--output", type=Path, default=None, help="Write markdown to file")
    args = ap.parse_args(argv)

    repo = number = None
    if args.pr:
        parsed = parse_pr_url(args.pr)
        if not parsed:
            print("error: --pr must look like https://github.com/owner/repo/pull/N", file=sys.stderr)
            return 2
        repo, number = parsed
    elif args.repo and args.pr_number:
        repo, number = args.repo, args.pr_number
    else:
        print("error: provide --pr URL or --repo + --pr-number", file=sys.stderr)
        return 2

    meta, diff = fetch_pr(repo, number)
    if not meta:
        print("error: failed to fetch PR metadata", file=sys.stderr)
        return 1

    risks = scan_diff(diff)
    review = Review(
        pr_url=meta.get("html_url") or f"https://github.com/{repo}/pull/{number}",
        title=meta.get("title") or "(untitled)",
        author=(meta.get("user") or {}).get("login") or "unknown",
        files_changed=meta.get("changed_files") or 0,
        additions=meta.get("additions") or 0,
        deletions=meta.get("deletions") or 0,
        summary=build_summary(meta, diff),
        risks=risks,
        suggestions=build_suggestions(risks, diff),
        confidence=confidence_for(meta, risks, diff),
    )
    md = render(review)
    if args.output:
        args.output.write_text(md, encoding="utf-8")
        print(f"wrote {args.output}")
    else:
        sys.stdout.write(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
