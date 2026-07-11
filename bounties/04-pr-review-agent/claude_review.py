#!/usr/bin/env python3
"""claude-review — structured PR review from a GitHub PR URL or local diff.

Usage:
  python claude_review.py --pr https://github.com/owner/repo/pull/123
  python claude_review.py --diff path/to.diff
  python claude_review.py --pr URL --json

Requires: `gh` authenticated for --pr mode (or GITHUB_TOKEN).
Optional: ANTHROPIC_API_KEY for model-backed narrative; otherwise heuristic review.
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
from pathlib import Path
from typing import Any


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)


def parse_pr_url(url: str) -> tuple[str, str, int]:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise SystemExit(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr_diff(owner: str, repo: str, number: int) -> tuple[str, dict[str, Any]]:
    meta = json.loads(
        run(
            [
                "gh",
                "pr",
                "view",
                str(number),
                "--repo",
                f"{owner}/{repo}",
                "--json",
                "title,body,author,additions,deletions,changedFiles,files,baseRefName,headRefName,url",
            ]
        )
    )
    try:
        diff = run(["gh", "pr", "diff", str(number), "--repo", f"{owner}/{repo}"])
    except subprocess.CalledProcessError:
        diff = ""
        for f in meta.get("files") or []:
            diff += f"\n--- a/{f.get('path')}\n+++ b/{f.get('path')}\n"
    return diff, meta


def heuristic_review(diff: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    meta = meta or {}
    lines = diff.splitlines()
    plus = sum(1 for l in lines if l.startswith("+") and not l.startswith("+++"))
    minus = sum(1 for l in lines if l.startswith("-") and not l.startswith("---"))
    files = sorted(
        {
            re.sub(r"^[ab]/", "", l[4:])
            for l in lines
            if l.startswith("+++ ") or l.startswith("--- ")
        }
        - {"/dev/null", "dev/null"}
    )
    risks: list[str] = []
    suggestions: list[str] = []

    text = diff.lower()
    if re.search(r"\brm\s+-rf\b|drop\s+table|force.?push", text):
        risks.append("Destructive shell/SQL or force-push patterns appear in the diff.")
    if re.search(r"api[_-]?key|secret|password|private_key|BEGIN RSA", text, re.I):
        risks.append("Possible secrets or credentials in the patch — verify not real keys.")
    if plus + minus > 800:
        risks.append(f"Large diff (~+{plus}/-{minus}); harder to review thoroughly.")
    if any(f.endswith((".yml", ".yaml")) and "workflow" in f.replace("\\", "/") for f in files):
        risks.append("CI workflow changes — confirm permissions and supply-chain risk.")
    if not risks:
        risks.append("No high-severity automated red flags; still needs human judgment on logic.")

    if any(f.endswith("_test.go") or "test" in f.lower() for f in files):
        suggestions.append("Keep tests green in CI; extend coverage for new branches.")
    else:
        suggestions.append("Add or update automated tests for the changed behavior.")
    if any(f.endswith((".md", "README")) for f in files):
        suggestions.append("Docs updated — ensure commands/paths match the code.")
    else:
        suggestions.append("Consider a short README/changelog note if user-facing.")
    suggestions.append("Request review from a maintainer familiar with the touched modules.")

    title = meta.get("title") or "(local diff)"
    conf = "High" if plus + minus < 120 and len(files) <= 3 else "Medium" if plus + minus < 500 else "Low"
    summary = (
        f"PR “{title}” touches {len(files) or 'unknown'} file(s) "
        f"(~+{plus}/-{minus} lines). "
        f"Automated pass flags {len([r for r in risks if 'No high-severity' not in r])} risk signal(s) "
        f"and recommends follow-ups before merge."
    )
    if meta.get("url"):
        summary += f" Source: {meta['url']}."

    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": conf,
        "files": files[:40],
        "stats": {"additions": plus, "deletions": minus, "files": len(files)},
        "mode": "heuristic",
    }


def anthropic_review(diff: str, meta: dict[str, Any] | None) -> dict[str, Any] | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    prompt = {
        "model": model,
        "max_tokens": 1200,
        "messages": [
            {
                "role": "user",
                "content": (
                    "Review this GitHub PR diff. Reply with ONLY JSON keys: "
                    "summary (2-3 sentences string), risks (string array), "
                    "suggestions (string array), confidence (Low|Medium|High).\n\n"
                    f"META: {json.dumps(meta or {})}\n\nDIFF:\n{diff[:80000]}"
                ),
            }
        ],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(prompt).encode(),
        headers={
            "content-type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    text = "".join(
        b.get("text", "") for b in body.get("content", []) if b.get("type") == "text"
    )
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    data["mode"] = "anthropic"
    return data


def to_markdown(review: dict[str, Any]) -> str:
    risks = "\n".join(f"- {r}" for r in review.get("risks") or [])
    sugg = "\n".join(f"- {s}" for s in review.get("suggestions") or [])
    return (
        f"# PR Review\n\n"
        f"## Summary of changes\n\n{review.get('summary', '')}\n\n"
        f"## Identified risks\n\n{risks or '- (none)'}\n\n"
        f"## Improvement suggestions\n\n{sugg or '- (none)'}\n\n"
        f"## Confidence score\n\n**{review.get('confidence', 'Medium')}**\n\n"
        f"_Engine: {review.get('mode', 'unknown')}_\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(prog="claude-review")
    ap.add_argument("--pr", help="GitHub PR URL")
    ap.add_argument("--diff", help="Path to unified diff file")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown")
    ap.add_argument("--heuristic-only", action="store_true")
    args = ap.parse_args()

    meta: dict[str, Any] | None = None
    if args.pr:
        owner, repo, num = parse_pr_url(args.pr)
        diff, meta = fetch_pr_diff(owner, repo, num)
    elif args.diff:
        diff = Path(args.diff).read_text(encoding="utf-8", errors="replace")
    else:
        ap.error("provide --pr or --diff")

    review = None
    if not args.heuristic_only:
        review = anthropic_review(diff, meta)
    if not review:
        review = heuristic_review(diff, meta)

    if args.json:
        print(json.dumps(review, indent=2))
    else:
        print(to_markdown(review))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
