#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
from collections import Counter


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout


def parse_pr_url(url: str):
    m = re.match(r"https://github.com/([^/]+)/([^/]+)/pull/(\d+)", url)
    if not m:
        raise ValueError("PR URL format invalid. Expected https://github.com/owner/repo/pull/123")
    return m.group(1), m.group(2), int(m.group(3))


def fetch_pr(owner, repo, number):
    base = f"repos/{owner}/{repo}/pulls/{number}"
    pr = json.loads(run(["gh", "api", base]))
    files = json.loads(run(["gh", "api", f"{base}/files?per_page=100"]))
    return pr, files


def infer_risks(files):
    risks = []
    names = [f.get("filename", "") for f in files]
    patches = "\n".join([f.get("patch", "") or "" for f in files])

    if any("auth" in n.lower() or "login" in n.lower() for n in names):
        risks.append("Authentication/authorization path touched; verify access-control tests.")
    if any("migrat" in n.lower() or "schema" in n.lower() for n in names):
        risks.append("Schema/migration changes can break backward compatibility.")
    if any("config" in n.lower() or ".env" in n.lower() for n in names):
        risks.append("Configuration changes may impact deployment/runtime defaults.")
    if "TODO" in patches or "FIXME" in patches:
        risks.append("Patch contains TODO/FIXME markers; possible unfinished behavior.")
    if any(f.get("changes", 0) > 300 for f in files):
        risks.append("Large file-level diff increases review escape risk.")
    if not risks:
        risks.append("No high-risk hotspot detected from filenames/diff metadata; run normal regression checks.")
    return risks


def infer_suggestions(files):
    sugg = [
        "Add/expand tests for changed logic paths, including edge cases and failure modes.",
        "Include before/after behavior notes in PR description for faster reviewer validation.",
    ]
    exts = Counter((f.get("filename", "").split(".")[-1].lower() if "." in f.get("filename", "") else "") for f in files)
    if exts.get("py") or exts.get("js") or exts.get("ts"):
        sugg.append("Run static checks/linting and attach command output in PR comments.")
    return sugg


def confidence(files):
    total_changes = sum(f.get("changes", 0) for f in files)
    if total_changes < 80:
        return "High"
    if total_changes < 250:
        return "Medium"
    return "Low"


def summarize(pr, files):
    file_count = len(files)
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    return (
        f"PR #{pr['number']} updates {file_count} file(s) with {additions} additions and {deletions} deletions. "
        f"Changes are focused around '{pr.get('title','(no title)')}'. "
        "Review should prioritize correctness, regressions, and test coverage on touched modules."
    )


def render(pr, files):
    s = summarize(pr, files)
    r = infer_risks(files)
    g = infer_suggestions(files)
    c = confidence(files)

    out = []
    out.append("## PR Review")
    out.append("")
    out.append("### Summary of changes")
    out.append(s)
    out.append("")
    out.append("### Identified risks")
    for x in r:
        out.append(f"- {x}")
    out.append("")
    out.append("### Improvement suggestions")
    for x in g:
        out.append(f"- {x}")
    out.append("")
    out.append(f"### Confidence score\n**{c}**")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True, help="GitHub PR URL")
    args = ap.parse_args()

    owner, repo, number = parse_pr_url(args.pr)
    pr, files = fetch_pr(owner, repo, number)
    print(render(pr, files))


if __name__ == "__main__":
    main()
