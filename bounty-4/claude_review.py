#!/usr/bin/env python3
"""Review a GitHub pull request with Claude Code."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

PR_URL_RE = re.compile(
    r"^https://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)/pull/(?P<number>\d+)/?$"
)
REQUIRED_HEADINGS = (
    "## Summary",
    "## Risks",
    "## Improvement suggestions",
    "## Confidence",
)

class ReviewError(RuntimeError):
    pass


def run(cmd: Sequence[str], *, input_text: str | None = None) -> str:
    try:
        result = subprocess.run(
            list(cmd), input=input_text, text=True, capture_output=True, check=False
        )
    except OSError as exc:
        raise ReviewError(f"unable to execute {cmd[0]}: {exc}") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ReviewError(f"{cmd[0]} failed ({result.returncode}): {detail}")
    return result.stdout


def validate_pr_url(value: str) -> str:
    if not PR_URL_RE.match(value):
        raise argparse.ArgumentTypeError(
            "expected https://github.com/OWNER/REPO/pull/NUMBER"
        )
    return value.rstrip("/")


def fetch_pr(pr_url: str) -> tuple[dict, str]:
    metadata_raw = run(
        [
            "gh", "pr", "view", pr_url, "--json",
            "title,body,author,baseRefName,headRefName,files,additions,deletions,url",
        ]
    )
    try:
        metadata = json.loads(metadata_raw)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"gh returned invalid PR metadata: {exc}") from exc
    diff = run(["gh", "pr", "diff", pr_url])
    return metadata, diff


def clip_diff(diff: str, max_bytes: int) -> tuple[str, bool]:
    encoded = diff.encode("utf-8")
    if len(encoded) <= max_bytes:
        return diff, False
    clipped = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return clipped + "\n\n[DIFF TRUNCATED BY claude-review]\n", True


def build_prompt(metadata: dict, diff: str, truncated: bool) -> str:
    files = metadata.get("files") or []
    file_names = [f.get("path", "?") for f in files]
    truncation_note = (
        "The diff was truncated. Lower confidence if omitted code could change conclusions."
        if truncated else "The complete diff is included."
    )
    return f"""You are a careful senior code reviewer. Review only evidence present below.
Do not invent runtime behavior, tests, or vulnerabilities.

Return Markdown with EXACTLY these sections:
## Summary
Write 2-3 sentences describing the change and its intent.

## Risks
- List concrete risks supported by the diff.
- If none are evident, write "- No material risks identified from the supplied diff."

## Improvement suggestions
- List actionable improvements.
- If none are needed, write "- No blocking improvements identified."

## Confidence
Write exactly one of: Low, Medium, High.

PR: {metadata.get('url', '')}
Title: {metadata.get('title', '')}
Base: {metadata.get('baseRefName', '')}
Head: {metadata.get('headRefName', '')}
Author: {(metadata.get('author') or {}).get('login', '')}
Changes: +{metadata.get('additions', 0)} / -{metadata.get('deletions', 0)}
Files: {', '.join(file_names)}
Diff note: {truncation_note}

--- BEGIN DIFF ---
{diff}
--- END DIFF ---
"""

def invoke_claude(prompt: str, claude_bin: str) -> str:
    executable = shutil.which(claude_bin) if os.sep not in claude_bin else claude_bin
    if not executable:
        raise ReviewError(
            f"Claude Code executable '{claude_bin}' not found. "
            "Install Claude Code or pass --claude-bin."
        )
    return run([executable, "-p", prompt, "--output-format", "text"]).strip()


def validate_review(review: str) -> None:
    missing = [heading for heading in REQUIRED_HEADINGS if heading not in review]
    if missing:
        raise ReviewError("Claude output is missing sections: " + ", ".join(missing))
    confidence = re.search(
        r"(?ms)^## Confidence\s*\n\s*(Low|Medium|High)\s*$", review
    )
    if not confidence:
        raise ReviewError("Confidence must be exactly Low, Medium, or High")

def post_review(pr_url: str, review: str) -> None:
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".md", delete=False
    ) as handle:
        handle.write(review)
        body_path = handle.name
    try:
        run(["gh", "pr", "comment", pr_url, "--body-file", body_path])
    finally:
        Path(body_path).unlink(missing_ok=True)

def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", required=True, type=validate_pr_url)
    parser.add_argument("--post", action="store_true", help="post review to the PR")
    parser.add_argument("--claude-bin", default=os.environ.get("CLAUDE_BIN", "claude"))
    parser.add_argument("--max-diff-bytes", type=int, default=120_000)
    return parser.parse_args(argv)

def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_diff_bytes < 1:
        raise ReviewError("--max-diff-bytes must be positive")
    metadata, diff = fetch_pr(args.pr)
    diff, truncated = clip_diff(diff, args.max_diff_bytes)
    review = invoke_claude(build_prompt(metadata, diff, truncated), args.claude_bin)
    validate_review(review)
    print(review)
    if args.post:
        post_review(args.pr, review)
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReviewError as exc:
        print(f"claude-review: {exc}", file=sys.stderr)
        raise SystemExit(2)
