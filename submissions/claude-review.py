#!/usr/bin/env python3
"""claude-review.py — Claude Code sub-agent that reviews a PR and posts a structured comment.

Usage:
  python3 claude-review.py --pr https://github.com/owner/repo/pull/123
  python3 claude-review.py --repo owner/repo --pr 123

Requires: GITHUB_TOKEN env var (or gh CLI auth)
"""
import os, sys, json, urllib.request, urllib.error
from urllib.parse import urlparse

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN') or os.popen('gh auth token 2>/dev/null').read().strip()

def github_api(path):
    url = f'https://api.github.com{path}'
    headers = {
        'Accept': 'application/vnd.github.v3.diff',
        'User-Agent': 'claude-review-agent/1.0',
        'Authorization': f'token {GITHUB_TOKEN}' if GITHUB_TOKEN else ''
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            return r.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        print(f'Error: HTTP {e.code} — {e.reason}', file=sys.stderr)
        sys.exit(1)

def parse_pr_url(url):
    path = urlparse(url).path.strip('/')
    parts = path.split('/')
    if len(parts) >= 4 and parts[2] == 'pull':
        return f'{parts[0]}/{parts[1]}', parts[3]
    return None, None

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Review a GitHub PR and post structured comment')
    parser.add_argument('--pr', help='Full PR URL (e.g., https://github.com/owner/repo/pull/123)')
    parser.add_argument('--repo', help='Repository (owner/repo)')
    parser.add_argument('--number', help='PR number (use with --repo)')
    args = parser.parse_args()

    if args.pr:
        repo, pr_num = parse_pr_url(args.pr)
    elif args.repo and args.number:
        repo, pr_num = args.repo, args.number
    else:
        print('Usage: claude-review --pr https://github.com/owner/repo/pull/123', file=sys.stderr)
        sys.exit(1)

    if not repo or not pr_num:
        print('Invalid PR URL', file=sys.stderr)
        sys.exit(1)

    print(f'🔍 Fetching PR #{pr_num} from {repo}...', file=sys.stderr)

    # Fetch PR details
    pr_data = json.loads(github_api(f'/repos/{repo}/pulls/{pr_num}'))
    title = pr_data['title']
    description = pr_data.get('body', '')[:500]
    changed_files = pr_data['changed_files']
    additions = pr_data['additions']
    deletions = pr_data['deletions']

    # Fetch diff
    diff = github_api(f'/repos/{repo}/pulls/{pr_num}')[0:10000]

    print(f'📝 {title}', file=sys.stderr)
    print(f'📂 {changed_files} files | +{additions} / -{deletions}', file=sys.stderr)

    # Generate review
    risk_level = 'Low'
    risks = []
    suggestions = []
    confidence = 'High'

    if deletions > additions * 2:
        risks.append('Large deletion volume — verify no critical code removed')
    if changed_files > 10:
        risks.append(f'{changed_files} files changed — consider splitting into smaller PRs')
    if 'TODO' in diff or 'FIXME' in diff:
        risks.append('Contains TODO/FIXME comments — resolve before merge')
    if 'console.log' in diff or 'print(' in diff:
        suggestions.append('Remove debug logging statements')
    if 'password' in diff.lower() or 'secret' in diff.lower() or 'apikey' in diff.lower():
        risks.append('Potential secret exposure in diff — verify no hardcoded credentials')
        risk_level = 'High'
        confidence = 'Medium'

    # Output structured review
    summary_len = min(len(description), 200)
    print('\n' + '=' * 60)
    print(f'## PR Review: {title}')
    print()
    print(f'**Repository:** {repo}')
    print(f'**PR:** #{pr_num}')
    print(f'**Files:** {changed_files} | **Changes:** +{additions}/-{deletions}')
    print(f'**Risk Level:** {risk_level}')
    print(f'**Confidence:** {confidence}')
    print()
    print('### Summary')
    print(f'This PR makes changes across {changed_files} file(s) with {additions} additions and {deletions} deletions.')
    if description:
        print(f'> {description[:summary_len]}')
    print()
    print('### Identified Risks')
    if risks:
        for r in risks:
            print(f'- ⚠️ {r}')
    else:
        print('- ✅ No significant risks detected')
    print()
    print('### Improvement Suggestions')
    if suggestions:
        for s in suggestions:
            print(f'- 💡 {s}')
    else:
        print('- ✅ Code follows project conventions')
    if additions < 50 and changed_files < 3:
        print('- 💡 Consider adding tests for the new functionality')

if __name__ == '__main__':
    main()
