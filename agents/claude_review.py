#!/usr/bin/env python3
"""CLI: structured PR review for GitHub pull requests."""
import argparse
import json
import re
import sys
import urllib.request

TEMPLATE = """## PR Review (automated)

### Summary
{summary}

### Risks
{risks}

### Suggestions
{suggestions}

### Confidence: {confidence}
"""


def fetch_pr(pr_url: str) -> dict:
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url.strip())
    if not m:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner, repo, num = m.group(1), m.group(2), m.group(3)
    api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}"
    req = urllib.request.Request(api, headers={"Accept": "application/vnd.github+json", "User-Agent": "missione-claude-review"})
    with urllib.request.urlopen(req, timeout=20) as r:
        pr = json.loads(r.read())
    files_api = f"https://api.github.com/repos/{owner}/{repo}/pulls/{num}/files"
    req2 = urllib.request.Request(files_api, headers={"Accept": "application/vnd.github+json", "User-Agent": "missione-claude-review"})
    with urllib.request.urlopen(req2, timeout=20) as r:
        files = json.loads(r.read())
    return {"pr": pr, "files": files}


def analyze(data: dict) -> str:
    pr = data["pr"]
    files = data["files"]
    title = pr.get("title", "")
    body = pr.get("body") or ""
    changed = len(files)
    additions = sum(f.get("additions", 0) for f in files)
    deletions = sum(f.get("deletions", 0) for f in files)
    filenames = [f.get("filename", "") for f in files[:10]]

    summary = (
        f"This PR \"{title}\" modifies {changed} file(s) (+{additions}/-{deletions}). "
        f"Key paths: {', '.join(filenames[:5]) or 'n/a'}. "
        f"Scope appears {'broad' if changed > 15 else 'focused'}."
    )

    risks = []
    if any(f.get("filename", "").endswith((".env", "secrets", "credentials")) for f in files):
        risks.append("Sensitive config files touched — verify no secrets committed.")
    if deletions > additions * 2 and deletions > 200:
        risks.append("Large deletion volume — regression risk.")
    if any("package-lock" in f.get("filename", "") or "yarn.lock" in f.get("filename", "") for f in files):
        risks.append("Lockfile changes — dependency supply-chain review needed.")
    if not risks:
        risks.append("No critical patterns detected; standard review recommended.")

    suggestions = []
    if changed > 20:
        suggestions.append("Consider splitting into smaller PRs for easier review.")
    if not body.strip():
        suggestions.append("Add PR description explaining motivation and test plan.")
    suggestions.append("Confirm CI passes and add tests for changed behavior.")
    if any(f.get("filename", "").endswith(".py") for f in files):
        suggestions.append("Run linter and type checker on Python changes.")

    confidence = "Low" if changed > 30 else "Medium" if changed > 8 else "High"

    return TEMPLATE.format(
        summary=summary,
        risks="\n".join(f"- {r}" for r in risks),
        suggestions="\n".join(f"- {s}" for s in suggestions),
        confidence=confidence,
    )


def main():
    parser = argparse.ArgumentParser(description="Structured GitHub PR review")
    parser.add_argument("--pr", required=True, help="GitHub PR URL")
    args = parser.parse_args()
    try:
        data = fetch_pr(args.pr)
        print(analyze(data))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
