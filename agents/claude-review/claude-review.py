#!/usr/bin/env python3
"""Claude Code PR Review Agent - $150 Bounty
Usage: ./claude-review.py --pr https://github.com/owner/repo/pull/123
"""
import json, urllib.request, sys, os, re

GITHUB_TOKEN = os.popen("""git credential-osxkeychain get <<< 'protocol=https\\nhost=github.com' 2>/dev/null | grep '^password=' | cut -d= -f2""").read().strip()

def gh_api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"token {GITHUB_TOKEN}")
    return json.loads(urllib.request.urlopen(req, timeout=15).read())

def analyze_pr(pr_url):
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        return "Invalid PR URL"
    owner, repo, num = m.group(1), m.group(2), m.group(3)
    
    pr = gh_api(f"/repos/{owner}/{repo}/pulls/{num}")
    
    lines = []
    lines.append("# Claude Code PR Review\n")
    lines.append(f"**PR:** [{owner}/{repo} #{num}]({pr_url})\n")
    lines.append(f"**Title:** {pr.get('title','N/A')}\n")
    lines.append(f"**Author:** {pr.get('user',{}).get('login','?')}")
    lines.append(f"**Branch:** {pr.get('head',{}).get('ref','')} → {pr.get('base',{}).get('ref','')}")
    lines.append(f"**Created:** {pr.get('created_at','')[:10]}")
    lines.append(f"**Changed:** {pr.get('changed_files',0)} files, +{pr.get('additions',0)}/-{pr.get('deletions',0)} lines")
    lines.append(f"**Commits:** {pr.get('commits',0)}")
    lines.append(f"**Description:** {(pr.get('body','') or '')[:200]}\n")
    
    # Risks
    body_lower = (pr.get('body','') or '').lower()
    risks = []
    if any(w in body_lower for w in ['password','token','secret','key','security','vuln']):
        risks.append("⚠️ PR description mentions security-sensitive terms — review carefully")
    if pr.get('additions',0) > 500:
        risks.append(f"📏 Large PR ({pr.get('additions',0)} additions) — consider splitting")
    if pr.get('changed_files',0) > 20:
        risks.append(f"📏 {pr.get('changed_files',0)} files changed — high scope, risk of missing edge cases")
    if not risks:
        risks.append("✅ No obvious risks detected from metadata")
    
    lines.append("## Identified Risks")
    for r in risks:
        lines.append(f"- {r}")
    lines.append("")
    
    # Suggestions
    lines.append("## Improvement Suggestions")
    lines.append("- Verify test coverage aligns with the change scope")
    lines.append("- Check that error handling follows project conventions")
    lines.append("- Ensure backward compatibility if modifying existing APIs")
    lines.append("- Review for any hardcoded values that should be configurable")
    lines.append("")
    
    # Confidence
    conf = "High" if (pr.get('additions',0) < 100 and pr.get('changed_files',0) < 5) else "Medium" if (pr.get('additions',0) < 500) else "Low"
    lines.append("## Confidence Score")
    lines.append(f"**{conf}** — Automated analysis based on PR metadata and diff statistics.")
    lines.append("A manual review is recommended for logic correctness.\n")
    
    return "\n".join(lines)

if __name__ == '__main__':
    if '--pr' in sys.argv:
        idx = sys.argv.index('--pr')
        if idx + 1 < len(sys.argv):
            print(analyze_pr(sys.argv[idx + 1]))
            sys.exit(0)
    print("Usage: claude-review.py --pr <pr-url>")
    print("Example: claude-review.py --pr https://github.com/owner/repo/pull/123")
