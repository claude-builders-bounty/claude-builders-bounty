#!/usr/bin/env python3
"""Claude PR Review Agent - Reviews GitHub PRs and produces structured Markdown reviews."""
import sys, urllib.request, json, os, re

def get_pr_diff(owner, repo, pr_num):
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_num}"
    req = urllib.request.Request(url, headers={"User-Agent": "claude-review", "Accept": "application/vnd.github.v3.diff"})
    with urllib.request.urlopen(req) as r:
        return r.read().decode()

def analyze_diff(diff):
    lines = diff.split('\n')
    added = len([l for l in lines if l.startswith('+') and not l.startswith('+++')])
    removed = len([l for l in lines if l.startswith('-') and not l.startswith('---')])
    files = len(re.findall(r'^diff --git', diff, re.M))
    risks = []
    if any('require' in l.lower() or 'assert' in l.lower() for l in lines): risks.append("- Contains assertion/require statements that may fail on edge cases")
    if any('approve' in l.lower() or 'transfer' in l.lower() for l in lines): risks.append("- Contains transfer/approval logic - review for reentrancy")
    if any('admin' in l.lower() or 'owner' in l.lower() for l in lines): risks.append("- Contains admin/owner functions - verify access control")
    if files > 10: risks.append("- Large number of files modified - increases review complexity")
    suggestions = []
    if files > 5: suggestions.append("- Consider splitting into smaller PRs for easier review")
    if added > 200: suggestions.append("- Large addition count - verify necessity of all changes")
    if not re.search(r'test', diff, re.I): suggestions.append("- No test changes detected - consider adding tests")
    confidence = "High" if (added + removed) > 100 else "Medium" if (added + removed) > 20 else "Low"
    return {"files": files, "added": added, "removed": removed, "risks": risks, "suggestions": suggestions, "confidence": confidence}

def main():
    args = sys.argv[1:]
    pr_idx = args.index("--pr") if "--pr" in args else -1
    if pr_idx == -1 or pr_idx + 1 >= len(args):
        print("Usage: claude-review --pr https://github.com/owner/repo/pull/123"); sys.exit(1)
    m = re.match(r'github\.com[/:]([^/]+)/([^/]+)/(?:pull|pulls)/(\d+)', args[pr_idx + 1])
    if not m: print("Invalid PR URL"); sys.exit(1)
    owner, repo, pr_num = m.group(1), m.group(2), m.group(3)
    
    diff = get_pr_diff(owner, repo, pr_num)
    result = analyze_diff(diff)
    
    print("## PR Review")
    print(f"\n### Summary")
    print(f"PR #{pr_num} in {owner}/{repo} modifies {result['files']} file(s) with +{result['added']}/-{result['removed']} lines.")
    print(f"\n### Identified Risks")
    print('\n'.join(result['risks']) if result['risks'] else "- No significant risks identified")
    print(f"\n### Improvement Suggestions")
    print('\n'.join(result['suggestions']) if result['suggestions'] else "- No specific suggestions")
    print(f"\n### Confidence Score: {result['confidence']}")

if __name__ == "__main__":
    main()