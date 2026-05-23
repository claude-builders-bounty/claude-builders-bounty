#!/usr/bin/env python3
"""claude-review — Structured PR review generator
Usage: python3 claude-review.py --pr https://github.com/owner/repo/pull/123
       python3 claude-review.py --pr 123 --repo owner/repo
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--pr", required=True, help="PR number or URL")
    p.add_argument("--repo", help="owner/repo")
    p.add_argument("-o", "--output", help="Output file")
    return p.parse_args()

def gh(*args, **kw):
    r = subprocess.run(["gh"] + list(args), capture_output=True, text=True, timeout=kw.get("timeout", 30))
    if r.returncode != 0: print(f"gh error: {r.stderr}", file=sys.stderr)
    return r.stdout

def main():
    args = parse_args()
    pr_url = args.pr
    
    if "github.com" in pr_url:
        m = re.match(r'https://github\.com/([^/]+/[^/]+)/pull/(\d+)', pr_url)
        if not m: sys.exit("Invalid PR URL")
        repo, num = m.group(1), int(m.group(2))
    else:
        num = int(pr_url)
        if not args.repo: sys.exit("--repo required")
        repo = args.repo
    
    print(f"🔍 Analyzing PR #{num} in {repo}...", file=sys.stderr)
    
    meta = json.loads(gh("pr", "view", str(num), "--repo", repo,
        "--json", "title,author,additions,deletions,changedFiles,files"))
    diff = gh("pr", "diff", str(num), "--repo", repo)
    
    lines = diff.split("\n")
    files = set()
    adds = dels = 0
    for l in lines:
        if l.startswith("+++ b/"): files.add(l[6:])
        elif l.startswith("+" ) and not l.startswith("+++"): adds += 1
        elif l.startswith("-") and not l.startswith("---"): dels += 1
    
    issues = []
    if re.search(r'(TODO|FIXME|HACK)', diff): issues.append("Contains TODO/FIXME markers")
    if re.search(r'(console\.log|print\(|debugger)', diff): issues.append("Debug statements present")
    
    review = [
        "## 📋 PR Review",
        "",
        f"### Summary",
        f"**{len(files)} files** | **+{adds}/-{dels}** lines | by @{meta['author']['login']}",
        "",
        meta.get("title", ""),
        "",
        "### Files Changed",
    ]
    for f in sorted(files):
        review.append(f"- `{f}`")
    review.append("")
    
    if issues:
        review.append("### ⚠️ Issues")
        for i in issues: review.append(f"- ❌ {i}")
        review.append("")
    
    review.append("### 💡 Suggestions")
    review.append("- Verify error handling covers edge cases")
    review.append("- Check backward compatibility for API changes")
    review.append(f"- Run `npm run lint && npm test` before merge")
    review.append("")
    
    has_tests = any("test" in f.lower() or "spec" in f.lower() for f in files)
    review.append("### 🧪 Tests")
    review.append(f"- {'✅' if has_tests else '⚠️'} Test files {'included' if has_tests else 'not detected — consider adding'}")
    review.append("")
    
    output = "\n".join(review)
    
    if args.output:
        with open(args.output, "w") as f: f.write(output)
    else:
        print(output)

if __name__ == "__main__":
    main()
