#!/usr/bin/env python3
"""
claude-review — Claude Code PR Review Agent

Analyzes a GitHub Pull Request diff and produces a structured Markdown review
comment with summary, risks, suggestions, and a confidence score.

Usage:
    claude-review --pr https://github.com/owner/repo/pull/123
    claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
    claude-review --file /path/to/diff.patch
    claude-review                         # reads diff from stdin
"""

import argparse
import json
import os
import re
import sys
import urllib.request

# ── Risk patterns ──────────────────────────────────────────────────────────

HIGH_RISK_PATTERNS = [
    (r'password\s*=',              'Hardcoded password/credential'),
    (r'secret\s*=',                'Hardcoded secret'),
    (r'api_key\s*=',               'Hardcoded API key'),
    (r'token\s*=',                 'Possible hardcoded token'),
    (r'-----BEGIN\s+(RSA )?PRIVATE KEY-----', 'Embedded private key'),
    (r'subprocess\.(call|Popen)',   'Dangerous subprocess execution'),
    (r'os\.system\b',              'Dangerous system call'),
    (r'\bexec\(',                  'Dangerous exec call'),
    (r'\beval\(',                  'Dangerous eval call'),
    (r'DROP\s+(TABLE|DATABASE)',    'Destructive database operation'),
    (r'TRUNCATE\s',                'Bulk data deletion'),
    (r'rm\s+-rf',                  'Destructive filesystem operation'),
    (r'git push --force',          'Force push may rewrite history'),
    (r'innerHTML\s*=',             'Dangerous HTML injection'),
    (r'dangerouslySetInnerHTML',   'Dangerous React HTML injection'),
    (r'v-html=',                   'Dangerous Vue HTML injection'),
    (r'Access-Control-Allow-Origin:\s*\*', 'Overly permissive CORS'),
    (r'\.env\b',                   '.env file committed'),
]

MEDIUM_RISK_PATTERNS = [
    (r'\bTODO\b',                  'Unresolved TODO'),
    (r'\bFIXME\b',                 'Unresolved FIXME'),
    (r'\bHACK\b',                  'Unresolved HACK note'),
    (r'console\.(log|debug)',      'Stray console.log debug output'),
    (r'\bprint\(.*\)',             'Possible debug print statement'),
    (r'\.skip\(',                  'Skipped test indicator'),
    (r'\.only\(',                  'Focused test indicator (may skip other tests)'),
    (r'# type: ignore',            'Suppressed type error'),
    (r'@ts-ignore',                'Suppressed TypeScript error'),
    (r'sleep\(\d{3,}\)',           'Long sleep — possible race condition workaround'),
    (r'debugger\b',                'Stray debugger statement'),
]


# ── Fetch helpers ──────────────────────────────────────────────────────────

def _headers():
    """Return auth headers if GITHUB_TOKEN is set."""
    h = {'User-Agent': 'claude-review-agent/1.0'}
    token = os.environ.get('GITHUB_TOKEN', '')
    if token:
        h['Authorization'] = f'Bearer {token}'
    return h


def fetch_pr_data(pr_url: str):
    """Fetch PR metadata and diff from GitHub."""
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not m:
        raise ValueError(f'Invalid PR URL: {pr_url}')
    owner, repo, number = m.group(1), m.group(2), m.group(3)
    base = f'https://api.github.com/repos/{owner}/{repo}/pulls/{number}'

    h = _headers()
    # Metadata (JSON)
    md_req = urllib.request.Request(base, headers={**h, 'Accept': 'application/vnd.github.v3+json'})
    with urllib.request.urlopen(md_req, timeout=30) as r:
        meta = json.loads(r.read().decode('utf-8'))

    # Diff (text)
    diff_req = urllib.request.Request(base, headers={**h, 'Accept': 'application/vnd.github.v3.diff'})
    with urllib.request.urlopen(diff_req, timeout=30) as r:
        diff = r.read().decode('utf-8')

    return {
        'title': meta.get('title', ''),
        'body': (meta.get('body') or '')[:500],
        'author': meta.get('user', {}).get('login', 'unknown'),
        'number': number,
        'url': pr_url,
        'diff': diff,
    }


def fetch_diff_url(diff_url: str):
    """Fetch diff content from an arbitrary URL."""
    req = urllib.request.Request(diff_url, headers=_headers())
    with urllib.request.urlopen(req, timeout=30) as r:
        return {'diff': r.read().decode('utf-8'), 'url': diff_url, 'number': '', 'title': '', 'author': ''}


def read_diff_file(path: str):
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        return {'diff': f.read(), 'url': path, 'number': '', 'title': '', 'author': ''}


# ── Analysis engine ────────────────────────────────────────────────────────

def analyze_diff(diff: str):
    """Analyze a unified diff and return structured findings."""
    findings = {
        'summary': {'files_changed': 0, 'additions': 0, 'deletions': 0},
        'high_risks': [],
        'medium_risks': [],
        'suggestions': [],
        'files': {},
        'confidence': 'High',
    }

    current_file = ''
    file_add = file_del = 0

    for line in diff.split('\n'):
        fm = re.match(r'^\+\+\+\s+(?:b/)?(.+)', line)
        if fm:
            if current_file:
                findings['files'][current_file] = {'additions': file_add, 'deletions': file_del}
            current_file = fm.group(1)
            file_add = file_del = 0
            findings['summary']['files_changed'] += 1
            continue

        if line.startswith('+') and not line.startswith('+++'):
            file_add += 1
            findings['summary']['additions'] += 1
            content = line[1:].strip()
            for pat, desc in HIGH_RISK_PATTERNS:
                if re.search(pat, content, re.IGNORECASE):
                    findings['high_risks'].append({'file': current_file or 'unknown', 'line': content[:150], 'desc': desc})
            for pat, desc in MEDIUM_RISK_PATTERNS:
                if re.search(pat, content, re.IGNORECASE):
                    findings['medium_risks'].append({'file': current_file or 'unknown', 'line': content[:150], 'desc': desc})

        if line.startswith('-') and not line.startswith('---'):
            file_del += 1
            findings['summary']['deletions'] += 1

    if current_file:
        findings['files'][current_file] = {'additions': file_add, 'deletions': file_del}

    s = findings['summary']

    # Suggestions
    large = {f: d for f, d in findings['files'].items() if d['additions'] > 200}
    for f, d in large.items():
        findings['suggestions'].append(f'Consider splitting `{f}` into smaller files ({d["additions"]} lines added).')

    if s['additions'] > 1000:
        findings['suggestions'].append(f'PR is large ({s["additions"]} additions). Break it into smaller PRs for easier review.')

    has_test = any('test' in f.lower() or 'spec' in f.lower() or '__tests__' in f for f in findings['files'])
    if not has_test and s['additions'] > 50:
        findings['suggestions'].append('No test files detected. Consider adding tests for the changed logic.')

    has_docs = any('readme' in f.lower() or 'doc' in f.lower() or f.endswith('.md') for f in findings['files'])
    if not has_docs and s['files_changed'] > 3 and s['additions'] > 100:
        findings['suggestions'].append('Consider updating documentation (README, API docs, etc.) for these changes.')

    # Confidence score
    risk_weight = len(findings['high_risks']) * 3 + len(findings['medium_risks'])
    total = s['additions'] + s['deletions']
    if total == 0:
        findings['confidence'] = 'Low'
    elif risk_weight > 12:
        findings['confidence'] = 'Low'
    elif risk_weight > 4:
        findings['confidence'] = 'Medium'
    elif total > 1500:
        findings['confidence'] = 'Medium'
    else:
        findings['confidence'] = 'High'

    return findings


# ── Output formatter ───────────────────────────────────────────────────────

def format_review(pr: dict, findings: dict) -> str:
    """Build structured Markdown review comment."""
    lines = []
    s = findings['summary']

    lines.append('## 🤖 Claude Code PR Review')
    lines.append('')
    if pr.get('title'):
        lines.append(f'> **PR**: [{pr["number"]}]({pr["url"]}) — {pr["title"]}')
    else:
        lines.append(f'> Source: {pr["url"]}')
    if pr.get('author'):
        lines.append(f'> **Author**: @{pr["author"]}')
    lines.append('')
    lines.append('---')
    lines.append('')

    # ── Summary ──
    lines.append('### 📋 Summary')
    lines.append('')
    if pr.get('body'):
        lines.append(f'> {pr["body"]}')
        lines.append('')
    noun = 'files' if s['files_changed'] != 1 else 'file'
    lines.append(f'This PR changes **{s["files_changed"]}** {noun} (**+{s["additions"]}** / **−{s["deletions"]}** lines).')
    lines.append('')

    # ── Files Changed ──
    if findings.get('files'):
        lines.append('### 📂 Files Changed')
        lines.append('')
        lines.append('| File | + | − |')
        lines.append('|------|---|---|')
        for f, d in sorted(findings['files'].items()):
            lines.append(f'| `{f}` | +{d["additions"]} | −{d["deletions"]} |')
        lines.append('')

    # ── Issues Found ──
    hr = findings.get('high_risks', [])
    mr = findings.get('medium_risks', [])
    if hr:
        lines.append('### ⚠️ Issues Found')
        lines.append('')
        lines.append('**🔴 High Risk**')
        for risk in hr:
            lines.append(f'- **{risk["desc"]}** — `{risk["file"]}`')
            if risk['line']:
                lines.append(f'  ```')
                lines.append(f'  {risk["line"][:120]}')
                lines.append(f'  ```')
        lines.append('')
    if mr:
        if not hr:
            lines.append('### ⚠️ Issues Found')
            lines.append('')
        lines.append('**🟡 Medium Risk / Concerns**')
        for risk in mr:
            lines.append(f'- **{risk["desc"]}** — `{risk["file"]}`')
            if risk['line']:
                lines.append(f'  ```')
                lines.append(f'  {risk["line"][:120]}')
                lines.append(f'  ```')
        lines.append('')

    # ── Suggestions ──
    suggestions = findings.get('suggestions', [])
    if suggestions:
        lines.append('### 💡 Improvement Suggestions')
        lines.append('')
        for i, s_ in enumerate(suggestions, 1):
            lines.append(f'{i}. {s_}')
        lines.append('')

    # ── Confidence ──
    conf = findings.get('confidence', 'Medium')
    emoji = {'High': '🟢', 'Medium': '🟡', 'Low': '🔴'}
    lines.append('### ✅ Confidence Score')
    lines.append('')
    lines.append(f'**{emoji.get(conf, "🟡")} {conf}**')
    if conf == 'High':
        lines.append('Clean PR with minimal concerns. Ready for human review.')
    elif conf == 'Medium':
        lines.append('Some items to address before merge. Review the flagged issues above.')
    else:
        lines.append('Significant concerns detected. Requires thorough human review.')
    lines.append('')

    lines.append('---')
    lines.append('')
    lines.append('_Generated by [claude-review-agent](https://github.com/claude-builders-bounty/claude-builders-bounty/tree/main/agents/pr-reviewer) v1.0_')

    return '\n'.join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Claude Code PR Review Agent — analyzes PRs and produces structured Markdown reviews.',
    )
    parser.add_argument('--pr', metavar='URL', help='GitHub PR URL, e.g. https://github.com/owner/repo/pull/123')
    parser.add_argument('--file', metavar='PATH', help='Path to a local unified-diff file')
    parser.add_argument('--diff-url', metavar='URL', help='Direct URL to a diff/patch file')
    parser.add_argument('-o', '--output', metavar='FILE', help='Write review to FILE instead of stdout')
    parser.add_argument('--json', action='store_true', help='Also output raw analysis as JSON')
    args = parser.parse_args()

    pr = {}
    if args.pr:
        print(f'🔍 Fetching PR: {args.pr}', file=sys.stderr)
        pr = fetch_pr_data(args.pr)
        print(f'   Title: {pr["title"]}', file=sys.stderr)
    elif args.file:
        print(f'📄 Reading diff from file: {args.file}', file=sys.stderr)
        pr = read_diff_file(args.file)
    elif args.diff_url:
        print(f'🔗 Fetching diff: {args.diff_url}', file=sys.stderr)
        pr = fetch_diff_url(args.diff_url)
    else:
        if not sys.stdin.isatty():
            pr = {'diff': sys.stdin.read(), 'url': '<stdin>', 'number': '', 'title': '', 'author': ''}
        else:
            parser.print_help()
            sys.exit(1)

    if not pr.get('diff', '').strip():
        print('❌ No diff content found.', file=sys.stderr)
        sys.exit(1)

    print(f'⚙️  Analyzing diff ({len(pr["diff"])} bytes)...', file=sys.stderr)
    findings = analyze_diff(pr['diff'])
    report = format_review(pr, findings)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f'✅ Report written to: {args.output}', file=sys.stderr)
    else:
        print()
        print(report)

    if args.json:
        json_out = {**findings, 'pr_title': pr.get('title', ''), 'pr_url': pr.get('url', '')}
        json.dump(json_out, sys.stdout, indent=2, ensure_ascii=False)
        print()

    s = findings['summary']
    print(f'\n📊 Stats: {s["files_changed"]} files, +{s["additions"]}/−{s["deletions"]} lines, confidence={findings["confidence"]}', file=sys.stderr)


if __name__ == '__main__':
    main()
