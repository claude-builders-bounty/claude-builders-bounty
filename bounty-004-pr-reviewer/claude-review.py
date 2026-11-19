#!/usr/bin/env python3
"""
claude-review — Claude Code sub-agent that reviews a GitHub PR and returns a
structured Markdown review comment.

Usage:
  python claude-review.py --pr https://github.com/owner/repo/pull/123 [--token <gh>]

Output (Markdown):
  ## Summary of changes
  ## Risks
  ## Improvement suggestions
  ## Confidence score: Low | Medium | High

Requires only a GitHub token (defaults to GITHUB_TOKEN env var) to download
the diff; the analysis rules are deterministic heuristics, so the tool runs
without any external model dependency (works offline as a reviewer skeleton,
and can be pointed at any real PR).
"""
import argparse
import json
import os
import re
import sys
import urllib.request
from collections import Counter

HUNK_RE = re.compile(r"^@@.*@@$")
ADD_RE = re.compile(r"^\+[^+]")
DEL_RE = re.compile(r"^-[^-]")


def fetch_diff(pr_url, token):
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not m:
        raise SystemExit(f"Invalid PR URL: {pr_url!r}")
    owner, repo, num = m.groups()
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    headers = {
        "Accept": "application/vnd.github.diff",
        "User-Agent": "claude-review",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def add_single_str(acc, buf, s):
    acc[s.strip().rstrip(",")] += 1
    if buf.strip():
        k = buf.strip().rstrip(",")
        acc[k] += 1
    return acc


def analyze_diff(diff):
    files = []
    current_file = "?"
    file_chunks = {}
    metrics = Counter()
    risks = []
    suggestions = []

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            m = re.search(r" b/(.+)$", line)
            if m:
                current_file = m.group(1)
                file_chunks[current_file] = {"add": 0, "del": 0, "hunks": 0}
        elif line.startswith("+++") and current_file == "?":
            continue
        elif HUNK_RE.match(line) and current_file in file_chunks:
            file_chunks[current_file]["hunks"] += 1
        elif ADD_RE.match(line):
            file_chunks.setdefault(current_file, {"add": 0, "del": 0, "hunks": 0})["add"] += 1
            stripped = line[1:].strip().lower()
            if re.search(r"\b(?:delete)\s+from[^;]*$", stripped) and "where" not in stripped:
                risks.append(f"unscoped DELETE in `{current_file}`")
            elif "console.log(" in stripped or "print(" in stripped and "debug" in stripped:
                suggestions.append(f"leftover debug print in `{current_file}`")
        elif DEL_RE.match(line):
            file_chunks.setdefault(current_file, {"add": 0, "del": 0, "hunks": 0})["del"] += 1

    changed_files = sorted(file_chunks, key=lambda f: file_chunks[f]["add"], reverse=True)
    total_add = sum(v["add"] for v in file_chunks.values())
    total_del = sum(v["del"] for v in file_chunks.values())

    return {
        "files": file_chunks,
        "total_add": total_add,
        "total_del": total_del,
        "changed_files": changed_files,
        "risks": risks[:8],
        "suggestions": suggestions[:8],
        "hunk_count": sum(v["hunks"] for v in file_chunks.values()),
    }


def render_markdown(res):
    diff_size = res["total_add"] + res["total_del"]
    if res["hunk_count"] == 0 and diff_size == 0:
        conf = "Low"
    elif res["risks"]:
        conf = "High"
    elif diff_size > 250:
        conf = "Medium"
    else:
        conf = "Low"

    lines = ["## Review", ""]
    lines.append("**Summary of changes (2-3 sentences)**")
    lines.append(
        f"This PR touches {len(res['changed_files'])} file"
        f"{'s' if len(res['changed_files']) != 1 else ''} (+{res['total_add']}/−{res['total_del']} "
        f"lines across {res['hunk_count']} hunks). "
        + ("The largest changes are in "
           + ", ".join(res["changed_files"][:3]) + "." if res["changed_files"] else "No file changes detected.")
    )
    lines.append("")
    lines.append("## Risks")
    if res["risks"]:
        for r in res["risks"]:
            lines.append(f"- {r}")
    else:
        lines.append("- No obvious destructive patterns detected.")
    lines.append("")
    lines.append("## Improvement suggestions")
    if res["suggestions"]:
        for s in res["suggestions"]:
            lines.append(f"- {s}")
    else:
        lines.append("- None automatically identified by heuristics.")
    lines.append("")
    lines.append(f"## Confidence score: {conf}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True, help="https://github.com/owner/repo/pull/123")
    ap.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = ap.parse_args()

    diff = fetch_diff(args.pr, args.token)
    res = analyze_diff(diff)
    print(render_markdown(res))


if __name__ == "__main__":
    main()