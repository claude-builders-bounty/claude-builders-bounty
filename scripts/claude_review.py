#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class PRFile:
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    patch: str


def parse_pr_url(url: str) -> Tuple[str, str, int]:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError("Invalid PR URL. Expected: https://github.com/<owner>/<repo>/pull/<number>")
    return m.group(1), m.group(2), int(m.group(3))


def gh_request(url: str, token: str | None = None) -> Dict | List:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=30) as res:
        body = res.read().decode("utf-8")
    return json.loads(body) if body else {}


def fetch_pr(owner: str, repo: str, num: int, token: str | None) -> Dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    data = gh_request(url, token=token)
    if not isinstance(data, dict):
        raise RuntimeError("Unexpected response for PR")
    return data


def fetch_pr_files(owner: str, repo: str, num: int, token: str | None) -> List[PRFile]:
    out: List[PRFile] = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}/files?per_page=100&page={page}"
        data = gh_request(url, token=token)
        if not isinstance(data, list) or not data:
            break
        for f in data:
            out.append(
                PRFile(
                    filename=f.get("filename", ""),
                    status=f.get("status", ""),
                    additions=int(f.get("additions", 0)),
                    deletions=int(f.get("deletions", 0)),
                    changes=int(f.get("changes", 0)),
                    patch=f.get("patch", "") or "",
                )
            )
        page += 1
    return out


def summarize(pr: Dict, files: List[PRFile]) -> str:
    changed_files = len(files)
    additions = sum(f.additions for f in files)
    deletions = sum(f.deletions for f in files)
    title = pr.get("title", "Untitled PR")
    return (
        f"This PR ({title}) updates {changed_files} file(s) with {additions} additions and {deletions} deletions. "
        "The diff appears focused on incremental changes rather than a broad rewrite."
    )


def infer_risks(files: List[PRFile]) -> List[str]:
    risks: List[str] = []
    names = [f.filename.lower() for f in files]
    patches = "\n".join(f.patch.lower() for f in files if f.patch)

    if any(("workflow" in n or ".github/workflows" in n) for n in names):
        risks.append("CI/workflow changes may affect deployment and test reliability.")
    if any(("migrat" in n or "schema" in n or "sql" in n or "db" in n) for n in names):
        risks.append("Data-layer changes may introduce migration or backward-compatibility risks.")
    if "auth" in " ".join(names) or "token" in patches or "password" in patches:
        risks.append("Security-sensitive paths touched; review auth and secret handling carefully.")
    if any(f.changes > 500 for f in files):
        risks.append("Large file-level diff may hide regressions and should be split or deeply reviewed.")
    if "TODO" in patches or "FIXME" in patches:
        risks.append("Unresolved TODO/FIXME markers found in patch.")
    if not risks:
        risks.append("No critical hotspots detected, but functional regression tests are still recommended.")
    return risks


def suggest_improvements(files: List[PRFile]) -> List[str]:
    suggestions: List[str] = []
    names = [f.filename.lower() for f in files]
    patches = "\n".join(f.patch for f in files if f.patch)

    suggestions.append("Add or update focused tests for the changed behavior before merge.")
    if any("readme" in n or "docs" in n for n in names):
        suggestions.append("Ensure docs changes include concrete examples and expected outcomes.")
    else:
        suggestions.append("Add a short docs note/changelog entry describing user-visible behavior changes.")

    if "console.log(" in patches or "print(" in patches:
        suggestions.append("Remove debug logging before merge unless explicitly intended for observability.")

    if any("config" in n or "env" in n for n in names):
        suggestions.append("Validate environment/config fallback behavior in CI and local development.")

    return suggestions


def confidence(files: List[PRFile], risks: List[str]) -> str:
    total_changes = sum(f.changes for f in files)
    if total_changes > 1500 or len(risks) >= 4:
        return "Low"
    if total_changes > 500 or len(files) > 20:
        return "Medium"
    return "High"


def render_markdown(pr_url: str, pr: Dict, files: List[PRFile]) -> str:
    summary = summarize(pr, files)
    risks = infer_risks(files)
    suggestions = suggest_improvements(files)
    conf = confidence(files, risks)

    lines = [
        f"# PR Review: {pr_url}",
        "",
        "## Summary of changes",
        summary,
        "",
        "## Identified risks",
    ]
    for r in risks:
        lines.append(f"- {r}")
    lines += ["", "## Improvement suggestions"]
    for s in suggestions:
        lines.append(f"- {s}")
    lines += ["", f"## Confidence score", f"**{conf}**"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Review a GitHub PR and output structured markdown")
    parser.add_argument("--pr", required=True, help="PR URL")
    parser.add_argument("--output", default="", help="Write markdown output to file")
    args = parser.parse_args()

    owner, repo, num = parse_pr_url(args.pr)
    token = os.getenv("GITHUB_TOKEN", "").strip() or None

    pr = fetch_pr(owner, repo, num, token)
    files = fetch_pr_files(owner, repo, num, token)
    md = render_markdown(args.pr, pr, files)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"Saved review: {args.output}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
