#!/usr/bin/env python3
"""Structured PR review generator for Claude Code bounty #4."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("$env:"):
            body = line.removeprefix("$env:").strip()
            key, value = body.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        else:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def parse_pr_url(url: str) -> tuple[str, str, int]:
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not match:
        raise SystemExit(f"Invalid PR URL: {url}")
    return match.group(1), match.group(2), int(match.group(3))


def api_get(url: str, token: str) -> dict | list:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "claude-review",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def fetch_pr_context(owner: str, repo: str, number: int, token: str) -> dict:
    pr = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}", token)
    files = api_get(f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/files?per_page=100", token)
    return {"pr": pr, "files": files}


def analyze(context: dict) -> str:
    pr = context["pr"]
    files = context["files"]
    risks: list[str] = []
    suggestions: list[str] = []

    filenames = [f.get("filename", "") for f in files]
    patch_blob = "\n".join(f.get("patch") or "" for f in files)

    if any(name.startswith(".github/workflows/") for name in filenames):
      risks.append("Touches GitHub Actions workflows; verify permissions and secret usage.")
    if "test" not in patch_blob.lower() and len(files) > 1:
      suggestions.append("Consider adding or updating automated tests for the changed behavior.")
    if re.search(r"rm\s+-rf|DROP TABLE|push --force", patch_blob, re.I):
      risks.append("Diff contains potentially destructive command examples or strings.")
    if any(name.endswith(".md") for name in filenames) and len(files) <= 2:
      suggestions.append("Documentation-only change; confirm examples match the implementation.")

    if not risks:
      risks.append("No high-risk patterns detected in the diff heuristics.")
    if not suggestions:
      suggestions.append("Review naming and error messages for clarity before merge.")

    changed = ", ".join(f"`{name}`" for name in filenames[:8])
    if len(filenames) > 8:
      changed += ", ..."

    confidence = "High" if len(files) <= 3 else "Medium" if len(files) <= 10 else "Low"

    title = pr.get("title", "Untitled PR")
    author = pr.get("user", {}).get("login", "unknown")
    summary_sentences = [
        f"This PR ({title}) by @{author} modifies {len(files)} file(s), primarily touching {changed}.",
        "The diff was analyzed with heuristic checks for workflow edits, destructive command strings, and test coverage gaps.",
        f"Overall review confidence is **{confidence}** based on change size and detected patterns.",
    ]

    return "\n".join(
        [
            "## PR Review",
            "",
            "### Summary",
            " ".join(summary_sentences[:2]),
            summary_sentences[2],
            "",
            "### Identified risks",
            *[f"- {item}" for item in risks],
            "",
            "### Improvement suggestions",
            *[f"- {item}" for item in suggestions],
            "",
            f"### Confidence score: {confidence}",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="claude-review")
    parser.add_argument("--pr", required=True, help="GitHub pull request URL")
    parser.add_argument("--out", help="Optional output markdown path")
    args = parser.parse_args()

    for env_path in (
        Path(__file__).resolve().parents[3] / "env.txt",
        Path(__file__).resolve().parents[3] / "scripts" / "env.txt",
    ):
        load_env(env_path)

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is required")

    owner, repo, number = parse_pr_url(args.pr)
    review = analyze(fetch_pr_context(owner, repo, number, token))

    if args.out:
        Path(args.out).write_text(review + "\n", encoding="utf-8")
        print(args.out)
    else:
        print(review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
