#!/usr/bin/env python3
"""claude-review: structured PR review CLI."""
import argparse, json, subprocess, sys

def gh(args):
    return subprocess.check_output(["gh"] + args, text=True, encoding="utf-8", errors="replace")

def fetch_pr(pr_url):
    # parse owner/repo/pull/number
    # use gh pr view
    diff = gh(["pr", "diff", pr_url])
    meta = gh(["pr", "view", pr_url, "--json", "title,body,additions,deletions,changedFiles"])
    return json.loads(meta), diff

def analyze(meta, diff):
    files = []
    for line in diff.splitlines():
        if line.startswith("diff --git"):
            files.append(line.split()[-1].lstrip("b/"))
    additions = meta.get("additions", 0)
    deletions = meta.get("deletions", 0)
    risks = []
    if additions > 500:
        risks.append("Large change size (>500 additions) increases review burden.")
    if "password" in diff.lower() or "secret" in diff.lower() or "api_key" in diff.lower():
        risks.append("Possible secret or credential in diff — verify no secrets committed.")
    if "eval(" in diff or "exec(" in diff:
        risks.append("Use of eval/exec detected — potential code injection.")
    if not risks:
        risks.append("No obvious high-risk patterns detected by heuristic scan.")
    suggestions = []
    if "test" not in diff.lower():
        suggestions.append("Consider adding or updating tests for changed code.")
    if "README" not in diff and "docs" not in diff.lower():
        suggestions.append("Update documentation if public API changed.")
    suggestions.append("Keep PRs small and focused for easier review.")
    confidence = "High" if (additions + deletions) < 200 else ("Medium" if (additions+deletions) < 1000 else "Low")
    summary = f"PR changes {len(files)} file(s) with +{additions}/-{deletions} lines. Title: {meta.get('title','')}."
    return summary, risks, suggestions, confidence, files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pr", required=True, help="PR URL")
    ap.add_argument("--post", action="store_true", help="Post comment to PR")
    args = ap.parse_args()
    meta, diff = fetch_pr(args.pr)
    summary, risks, suggestions, confidence, files = analyze(meta, diff)
    md = []
    md.append("## Automated PR Review")
    md.append("")
    md.append(f"**Summary:** {summary}")
    md.append("")
    md.append("### Identified risks")
    for r in risks:
        md.append(f"- {r}")
    md.append("")
    md.append("### Improvement suggestions")
    for s in suggestions:
        md.append(f"- {s}")
    md.append("")
    md.append(f"**Confidence score:** {confidence}")
    md.append("")
    md.append(f"_Files changed ({len(files)}):_ " + ", ".join(f"`{f}`" for f in files[:10]))
    output = "\n".join(md)
    print(output)
    if args.post:
        subprocess.run(["gh", "pr", "comment", args.pr, "--body", output], check=True)

if __name__ == "__main__":
    main()
