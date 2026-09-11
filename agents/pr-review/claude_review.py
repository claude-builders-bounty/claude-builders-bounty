#!/usr/bin/env python3
"""claude-review: structured Markdown PR review agent (Opire #4).

Usage:
  python3 agents/pr-review/claude_review.py --pr https://github.com/owner/repo/pull/123
  python3 agents/pr-review/claude_review.py --diff path/to.diff --title "..."

Requires: gh CLI authenticated OR a unified diff file.
Optional: ANTHROPIC_API_KEY for live Claude narrative (falls back to heuristic review).
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
from typing import List, Optional, Tuple

RISK_PATTERNS = [
    (r"\brm\s+-rf\b", "Destructive shell rm -rf"),
    (r"\bDROP\s+TABLE\b", "SQL DROP TABLE"),
    (r"\bgit\s+push\s+--force\b", "Force-push"),
    (r"api[_-]?key|secret|password|private[_-]?key", "Possible secret material"),
    (r"eval\(|exec\(|subprocess\..*shell\s*=\s*True", "Dynamic code execution"),
    (r"curl\s+[^\n]*\|\s*(ba)?sh", "Pipe remote script to shell"),
    (r"0x[a-fA-F0-9]{64}", "Hard-coded high-entropy hex (possible key)"),
    (r"AKIA[0-9A-Z]{16}", "AWS access key pattern"),
    (r"-----BEGIN (RSA |OPENSSH )?PRIVATE KEY-----", "Private key block"),
]

IMPROVE_HINTS = [
    (r"TODO|FIXME|XXX", "Resolve leftover TODO/FIXME markers before merge"),
    (r"print\(|console\.log\(", "Remove debug logging from production paths"),
    (r"except:\s*$|except Exception:\s*pass", "Avoid bare/silent exception handlers"),
    (r"time\.sleep\(\s*[5-9]\d{2,}", "Long sleeps may hide race conditions — prefer explicit waits"),
    (r"localhost|127\.0\.0\.1", "Hard-coded localhost may break in CI/prod"),
]


@dataclass
class Finding:
    kind: str
    detail: str


@dataclass
class Review:
    title: str
    pr_url: str
    summary: str
    risks: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)
    confidence: str = "Medium"
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    model_note: str = "heuristic"


def parse_pr_url(url: str) -> Tuple[str, str, str]:
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", url.strip())
    if not m:
        raise SystemExit(f"Unsupported PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def run(cmd: List[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"cmd failed: {' '.join(cmd)}\n{p.stderr}")
    return p.stdout


def fetch_pr(pr_url: str) -> Tuple[str, str, str]:
    owner, repo, number = parse_pr_url(pr_url)
    meta = json.loads(run(["gh", "pr", "view", number, "-R", f"{owner}/{repo}",
                           "--json", "title,body,additions,deletions,changedFiles,files"]))
    diff = run(["gh", "pr", "diff", number, "-R", f"{owner}/{repo}"])
    title = meta.get("title") or f"PR #{number}"
    return title, diff, json.dumps(meta)


def score_diff(title: str, diff: str, pr_url: str = "") -> Review:
    added = len(re.findall(r"^\+", diff, re.M))
    removed = len(re.findall(r"^-", diff, re.M))
    files = len(set(re.findall(r"^diff --git a/(\S+)", diff, re.M)))
    risks: List[str] = []
    improvements: List[str] = []
    for pat, label in RISK_PATTERNS:
        if re.search(pat, diff, re.I | re.M):
            risks.append(label)
    for pat, label in IMPROVE_HINTS:
        if re.search(pat, diff, re.I | re.M):
            improvements.append(label)
    if files == 0 and not diff.strip():
        risks.append("Empty diff — nothing to review")
    if added + removed > 800:
        improvements.append("Large diff — consider splitting into smaller PRs for safer review")
    if not risks:
        improvements.append("Add or extend automated tests covering the changed paths")
    # summary
    touch = f"{files} file(s), +{added}/-{removed}"
    summary = (
        f"This PR ('{title}') changes {touch}. "
        f"Automated scan flagged {len(risks)} risk signal(s) and {len(improvements)} improvement(s). "
        f"Treat high-risk hits as merge blockers until cleared."
    )
    # confidence
    if len(risks) >= 3 or added + removed > 1500:
        conf = "Low"
    elif len(risks) == 0 and files <= 8:
        conf = "High"
    else:
        conf = "Medium"
    # optional Claude polish
    model_note = "heuristic"
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key and diff.strip():
        try:
            summary2, risks2, imps2, conf2 = call_claude(key, title, diff[:120000])
            summary, risks, improvements, conf = summary2, risks2 or risks, imps2 or improvements, conf2 or conf
            model_note = "claude+heuristic"
        except Exception as e:
            model_note = f"heuristic (claude failed: {type(e).__name__})"
    return Review(title=title, pr_url=pr_url, summary=summary, risks=risks,
                  improvements=improvements, confidence=conf, files_changed=files,
                  lines_added=added, lines_removed=removed, model_note=model_note)


def call_claude(api_key: str, title: str, diff: str) -> Tuple[str, List[str], List[str], str]:
    body = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 900,
        "messages": [{
            "role": "user",
            "content": (
                "Review this git PR diff. Reply ONLY compact JSON with keys "
                "summary (2-3 sentences string), risks (string array), improvements (string array), "
                "confidence (Low|Medium|High).\n"
                f"TITLE: {title}\nDIFF:\n{diff}"
            ),
        }],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        payload = json.loads(r.read().decode())
    text = "".join(p.get("text", "") for p in payload.get("content", []) if p.get("type") == "text")
    m = re.search(r"\{[\s\S]*\}", text)
    data = json.loads(m.group(0) if m else text)
    return (
        str(data.get("summary") or ""),
        list(data.get("risks") or []),
        list(data.get("improvements") or []),
        str(data.get("confidence") or "Medium"),
    )


def render_markdown(rev: Review) -> str:
    risks = "\n".join(f"- {r}" for r in rev.risks) or "- None flagged by automated scan"
    imps = "\n".join(f"- {i}" for i in rev.improvements) or "- None"
    lines = [
        f"# PR Review: {rev.title}",
        "",
        f"**Source:** {rev.pr_url or '(local diff)'}",
        f"**Stats:** {rev.files_changed} files, +{rev.lines_added}/-{rev.lines_removed}",
        f"**Engine:** {rev.model_note}",
        "",
        "## Summary of changes",
        rev.summary,
        "",
        "## Identified risks",
        risks,
        "",
        "## Improvement suggestions",
        imps,
        "",
        f"## Confidence score: {rev.confidence}",
        "",
    ]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="claude-review")
    ap.add_argument("--pr", help="GitHub PR URL")
    ap.add_argument("--diff", help="Path to unified diff")
    ap.add_argument("--title", default="local-diff")
    ap.add_argument("-o", "--output", help="Write markdown to path")
    args = ap.parse_args(argv)

    if not args.pr and not args.diff:
        ap.error("provide --pr or --diff")

    if args.pr:
        title, diff, _ = fetch_pr(args.pr)
        pr_url = args.pr
    else:
        title = args.title
        diff = Path(args.diff).read_text(encoding="utf-8", errors="replace")
        pr_url = ""

    rev = score_diff(title, diff, pr_url=pr_url)
    md = render_markdown(rev)
    if args.output:
        Path(args.output).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
