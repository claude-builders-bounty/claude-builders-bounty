#!/usr/bin/env python3
"""claude-review: structured Markdown review of a GitHub PR.

Usage:
  python claude_review.py --pr https://github.com/owner/repo/pull/123
  python claude_review.py --pr owner/repo#123
  python claude_review.py --diff path/to.diff   # offline

Needs: GitHub CLI (`gh`) authenticated, or GITHUB_TOKEN for API.
Heuristic analysis only (no paid LLM required) so it always runs offline-friendly.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class Review:
    summary: str
    risks: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    confidence: str = "Medium"
    meta: dict = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            "# PR Review",
            "",
            f"**Confidence:** {self.confidence}",
            "",
            "## Summary",
            self.summary.strip(),
            "",
            "## Identified risks",
        ]
        if self.risks:
            lines.extend(f"- {r}" for r in self.risks)
        else:
            lines.append("- None flagged by heuristic scan.")
        lines += ["", "## Improvement suggestions"]
        if self.suggestions:
            lines.extend(f"- {s}" for s in self.suggestions)
        else:
            lines.append("- No strong suggestions from static heuristics.")
        if self.meta:
            lines += ["", "## Meta"]
            for k, v in self.meta.items():
                lines.append(f"- **{k}:** {v}")
        lines.append("")
        return "\n".join(lines)


def parse_pr_ref(ref: str) -> tuple[str, str, int]:
    ref = ref.strip()
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([^/#]+)/([^/#]+)#(\d+)$", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    m = re.match(r"([^/#]+)/([^/#]+)/pull/(\d+)", ref)
    if m:
        return m.group(1), m.group(2), int(m.group(3))
    raise SystemExit(f"Cannot parse PR ref: {ref}")


def gh_api(path: str) -> dict | list:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        # try gh auth token
        try:
            token = subprocess.check_output(
                ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            token = ""
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "claude-review/1.0",
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def fetch_pr(owner: str, repo: str, number: int) -> tuple[dict, str]:
    pr = gh_api(f"/repos/{owner}/{repo}/pulls/{number}")
    # unified diff
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        try:
            token = subprocess.check_output(
                ["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            token = ""
    req = urllib.request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        headers={
            "User-Agent": "claude-review/1.0",
            "Accept": "application/vnd.github.v3.diff",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        diff = r.read().decode(errors="replace")
    return pr, diff


def analyze_diff(diff: str, title: str = "", body: str = "") -> Review:
    files = re.findall(r"^diff --git a/(.+?) b/", diff, re.M)
    added = len(re.findall(r"^\+[^+]", diff, re.M))
    removed = len(re.findall(r"^-[^-]", diff, re.M))
    risks: list[str] = []
    suggestions: list[str] = []

    dangerous = [
        (r"rm\s+-rf", "Shell snippet may delete trees recursively (`rm -rf`)."),
        (r"eval\s*\(|exec\s*\(|subprocess\..*shell\s*=\s*True", "Dynamic code execution or shell=True increases injection risk."),
        (r"api[_-]?key|secret|password\s*=\s*['\"][^'\"]+['\"]", "Possible hard-coded secret in the diff."),
        (r"BEGIN (RSA |OPENSSH )?PRIVATE KEY", "Private key material in the diff."),
        (r"--force|-f\b.*push|push\s+--force", "Force-push related change — history rewrite risk."),
        (r"DROP\s+TABLE|TRUNCATE\b", "Destructive SQL appears in the change."),
        (r"https?://localhost|127\.0\.0\.1", "Localhost URLs may be accidental in prod configs."),
    ]
    for pat, msg in dangerous:
        if re.search(pat, diff, re.I):
            risks.append(msg)

    if any(f.endswith((".env", "credentials.json", "id_rsa")) for f in files):
        risks.append("Sensitive-looking filenames touched — confirm nothing secret is committed.")

    if added + removed > 800:
        risks.append(f"Large diff (~+{added}/-{removed} lines) — harder to review thoroughly.")
        suggestions.append("Split into smaller PRs if possible for safer review and faster merge.")

    if not re.search(r"test_|_test\.|spec\.|describe\(", diff, re.I) and added > 40:
        suggestions.append("No obvious tests in the diff — add a focused test for the happy path and one failure case.")

    if any(f.endswith(".md") for f in files) and not any(
        "test" in f or f.endswith((".py", ".ts", ".js", ".go", ".rs")) for f in files
    ):
        suggestions.append("Docs/skill-only PR: include a short sample output or usage snippet in the PR body.")

    if re.search(r"TODO|FIXME|XXX", diff):
        suggestions.append("Resolve or ticket remaining TODO/FIXME markers before merge.")

    if not body.strip() and not title.strip():
        suggestions.append("Add a PR description explaining why and how you verified.")

    # Confidence heuristic
    conf = "High"
    if risks:
        conf = "Medium"
    if len(risks) >= 3 or added + removed > 1500:
        conf = "Low"
    if not files and not diff.strip():
        conf = "Low"
        risks.append("Empty or unreadable diff.")

    file_list = ", ".join(files[:12]) + ("…" if len(files) > 12 else "")
    summary = (
        f"This PR touches {len(files)} file(s) with roughly +{added}/-{removed} lines. "
        f"Primary paths: {file_list or 'n/a'}. "
        f"Title context: {title[:120] or 'n/a'}."
    )

    if not suggestions:
        suggestions.append("Looks tidy from static scan — a quick human pass on behavior is still worth it.")

    return Review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=conf,
        meta={
            "files_changed": len(files),
            "lines_added_approx": added,
            "lines_removed_approx": removed,
        },
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="claude-review")
    ap.add_argument("--pr", help="PR URL or owner/repo#n")
    ap.add_argument("--diff", help="Path to unified diff file")
    ap.add_argument("-o", "--output", help="Write Markdown to file")
    args = ap.parse_args(argv)

    title = body = ""
    diff = ""
    meta_extra = {}

    if args.diff:
        diff = Path(args.diff).read_text(encoding="utf-8", errors="replace")
        meta_extra["source"] = args.diff
    elif args.pr:
        owner, repo, num = parse_pr_ref(args.pr)
        try:
            pr, diff = fetch_pr(owner, repo, num)
        except urllib.error.HTTPError as e:
            print(f"GitHub API error: {e}", file=sys.stderr)
            return 1
        title = pr.get("title") or ""
        body = pr.get("body") or ""
        meta_extra = {
            "pr": f"{owner}/{repo}#{num}",
            "html_url": pr.get("html_url"),
            "user": (pr.get("user") or {}).get("login"),
        }
    else:
        ap.print_help()
        return 2

    review = analyze_diff(diff, title=title, body=body)
    review.meta.update(meta_extra)
    md = review.to_markdown()
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
