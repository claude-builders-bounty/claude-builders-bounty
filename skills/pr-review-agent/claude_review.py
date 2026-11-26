#!/usr/bin/env python3
"""claude-review — review a GitHub PR and print a structured Markdown review.

Usage:
  claude-review --pr https://github.com/owner/repo/pull/123 [--json] [--out FILE]

Fetches the PR diff via the `gh` CLI, runs deterministic heuristics, and emits:
  - Summary of changes
  - Identified risks
  - Improvement suggestions
  - Confidence: Low / Medium / High

No external API key required; uses gh authentication already on the machine.
"""
import argparse
import json
import os
import re
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def parse_pr(url):
    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        sys.exit(f"Invalid PR URL: {url}")
    return m.group(1), m.group(2), m.group(3)


def fetch(owner, repo, num):
    meta = run(["gh", "pr", "view", num, "--repo", f"{owner}/{repo}",
                "--json", "title,author,additions,deletions,changedFiles,body,state"])
    diff = run(["gh", "pr", "diff", num, "--repo", f"{owner}/{repo}"])
    if meta.returncode != 0:
        sys.exit("gh error: " + meta.stderr.strip())
    return json.loads(meta.stdout), diff.stdout


RISK_PATTERNS = [
    (r"\brm\s+-rf\b", "Destructive `rm -rf` present in the diff."),
    (r"\bDROP\s+TABLE\b", "`DROP TABLE` statement present — destructive schema change."),
    (r"\bTRUNCATE\b", "`TRUNCATE` present — irreversibly clears table data."),
    (r"git\s+push\s+--force", "Force-push referenced — risk of history overwrite."),
    (r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{6,}", "Possible hardcoded secret/credential."),
    (r"(?i)verify\s*=\s*False", "TLS verification disabled (`verify=False`)."),
    (r"(?i)eval\(|exec\(", "Dynamic code execution (`eval`/`exec`) — injection risk."),
    (r"(?i)subprocess\.(call|run|Popen)\([^)]*shell\s*=\s*True", "`shell=True` subprocess — command injection risk."),
    (r"(?i)chmod\s+777", "World-writable permissions (`chmod 777`)."),
    (r"(?i)SELECT\s+\*\s+FROM", "`SELECT *` — may fetch unnecessary columns."),
]


def analyse(meta, diff):
    files = re.findall(r"^diff --git a/(\S+) b/\S+", diff, re.M)
    added = [l for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")]
    removed = [l for l in diff.splitlines() if l.startswith("-") and not l.startswith("---")]

    risks = []
    for pat, msg in RISK_PATTERNS:
        if re.search(pat, diff):
            risks.append(msg)

    suggestions = []
    if not meta.get("body"):
        suggestions.append("PR description is empty — add context, motivation, and testing notes.")
    if len(added) > 400:
        suggestions.append(f"Large change (+{len(added)} lines) — consider splitting into smaller PRs.")
    if files and not any(f.endswith((".md",)) or "test" in f.lower() for f in files):
        suggestions.append("No tests or docs touched — consider adding a test for the new behaviour.")
    if any(f.endswith((".env", ".pem", ".key")) for f in files):
        suggestions.append("Sensitive file type changed — confirm no secrets are committed.")
    if not suggestions:
        suggestions.append("No blocking issues spotted by heuristics; human review still recommended for logic correctness.")

    # Confidence heuristic
    if risks:
        confidence = "Low"
    elif len(added) > 400 or len(files) > 15:
        confidence = "Medium"
    else:
        confidence = "High"

    summary = (f"This PR by @{meta.get('author',{}).get('login','?')} changes "
               f"{meta.get('changedFiles','?')} file(s) with +{meta.get('additions','?')}/-{meta.get('deletions','?')} lines. "
               f"It touches {', '.join(files[:5])}{'…' if len(files) > 5 else ''}.")
    return summary, files, risks, suggestions, confidence


def render(meta, summary, files, risks, suggestions, confidence, url):
    lines = []
    lines.append("## 🤖 Claude Code Review")
    lines.append("")
    lines.append(f"> **PR**: {meta.get('title','?')}  ")
    lines.append(f"> **URL**: {url}  ")
    lines.append(f"> **State**: {meta.get('state','?')}")
    lines.append("")
    lines.append("### 📋 Summary")
    lines.append(summary)
    lines.append("")
    lines.append("### ⚠️ Identified Risks")
    lines.extend([f"- {r}" for r in risks] or ["- None detected by heuristics."])
    lines.append("")
    lines.append("### 💡 Improvement Suggestions")
    lines.extend([f"- {s}" for s in suggestions])
    lines.append("")
    lines.append(f"### ✅ Confidence: {confidence}")
    lines.append("")
    lines.append(f"_Files changed: {len(files)} · heuristic review, not a substitute for human judgement._")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(prog="claude-review")
    ap.add_argument("--pr", required=True, help="GitHub PR URL")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    ap.add_argument("--out", help="write output to file")
    a = ap.parse_args()

    owner, repo, num = parse_pr(a.pr)
    meta, diff = fetch(owner, repo, num)
    summary, files, risks, suggestions, confidence = analyse(meta, diff)

    if a.json:
        out = json.dumps({
            "pr": a.pr, "title": meta.get("title"), "summary": summary,
            "files": files, "risks": risks, "suggestions": suggestions,
            "confidence": confidence,
        }, indent=2)
    else:
        out = render(meta, summary, files, risks, suggestions, confidence, a.pr)

    if a.out:
        open(a.out, "w").write(out)
        print(f"written: {a.out}")
    else:
        print(out)


if __name__ == "__main__":
    main()
