#!/usr/bin/env python3
"""PR review agent — emits structured summary / risks / suggestions / confidence."""
from __future__ import annotations
import argparse, json, re, sys, urllib.request

def fetch_pr(repo: str, number: int, token: str = "") -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{number}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "genie-pr-review"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def fetch_files(repo: str, number: int, token: str = "") -> list:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/pulls/{number}/files",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "genie-pr-review"},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def review(pr: dict, files: list) -> dict:
    names = [f.get("filename") or "" for f in files]
    risks = []
    if any(re.search(r"auth|password|secret|token", n, re.I) for n in names):
        risks.append("Touches auth/secret-related paths — verify no credential leakage.")
    if any(f.get("changes", 0) > 400 for f in files):
        risks.append("Large diff — prefer smaller reviewable commits.")
    if not files:
        risks.append("No files in PR.")
    suggestions = [
        "Confirm tests cover changed paths.",
        "Ensure PR description links the issue.",
    ]
    summary = (
        f"PR #{pr.get('number')}: {pr.get('title')} — "
        f"{len(files)} files changed by {((pr.get('user') or {}).get('login'))}."
    )
    confidence = 0.7 if files else 0.3
    return {
        "summary": summary,
        "risks": risks or ["No major automated risks detected."],
        "suggestions": suggestions,
        "confidence": confidence,
        "files": names[:40],
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--pr", type=int, required=True)
    ap.add_argument("--token", default="")
    args = ap.parse_args()
    pr = fetch_pr(args.repo, args.pr, args.token)
    files = fetch_files(args.repo, args.pr, args.token)
    out = review(pr, files)
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
