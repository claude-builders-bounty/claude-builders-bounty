#!/usr/bin/env python3
"""
Claude Code sub-agent for PR review.
Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
"""

import argparse, json, os, re, sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')

def fetch(url):
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'claude-review-agent'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        return json.loads(resp.read())

def fetch_diff(url):
    headers = {'Accept': 'application/vnd.github.diff', 'User-Agent': 'claude-review-agent'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'token {GITHUB_TOKEN}'
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        return resp.read().decode('utf-8')

def parse_pr_url(url):
    m = re.match(r'https://github\.com/([^/]+)/([^/]+)/pull/(\d+)', url)
    if not m:
        raise ValueError('Invalid PR URL format')
    return m.group(1), m.group(2), m.group(3)

def analyze_diff(diff_text):
    files = defaultdict(lambda: {'additions': 0, 'deletions': 0, 'changed_lines': []})
    current_file = None

    for line in diff_text.split('\n'):
        if line.startswith('+++ b/'):
            current_file = line[6:]
        elif line.startswith('--- a/'):
            continue
        elif current_file and line.startswith('+') and not line.startswith('+++'):
            files[current_file]['additions'] += 1
            files[current_file]['changed_lines'].append(('+', line[1:]))
        elif current_file and line.startswith('-') and not line.startswith('---'):
            files[current_file]['deletions'] += 1
            files[current_file]['changed_lines'].append(('-', line[1:]))
        elif line.startswith('diff --git'):
            current_file = None

    return files

def classify_changes(files):
    risk_patterns = {
        'high': [
            (r'token|secret|password|api.?key|credential', 'Hardcoded credential detected'),
            (r'exec\(|eval\(|subprocess\.', 'Dynamic code execution'),
            (r'DROP\s+TABLE|DROP\s+DATABASE', 'Destructive SQL operation'),
            (r'rm\s+-rf|--force', 'Destructive file operation'),
            (r'raw\(|mark_safe', 'XSS vulnerability'),
            (r'__repr__|__str__.*=.*f"', 'String formatting in dunder methods'),
        ],
        'medium': [
            (r'(?<!\w)todo|fixme|hack|workaround(?!\s*:)', 'Unresolved TODO/FIXME'),
            (r'except\s*:', 'Bare except clause'),
            (r'#\s*type:\s*ignore', 'Type check suppressed'),
            (r'\bprint\(', 'Debug print statement'),
            (r'migration|schema.*change|alter\s+table', 'Schema change (requires migration)'),
            (r'\.env|credentials\.', 'Possible credential file reference'),
            (r'import\s+\*\s*$', 'Wildcard import'),
        ],
        'low': [
            (r'\${{|process\.env', 'Environment variable reference'),
            (r'pragma|workaround|temp', 'Temporary workaround'),
            (r'(?<![\w/])v\d|version|bump', 'Version bump'),
        ],
    }

    risks = []
    improvements = []
    total_additions = sum(f['additions'] for f in files.values())
    total_deletions = sum(f['deletions'] for f in files.values())
    changed_files = len(files)

    for fname, fdata in files.items():
        for line_type, content in fdata['changed_lines']:
            for severity, patterns in risk_patterns.items():
                for pattern, description in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        risks.append({'file': fname, 'line': content[:80], 'severity': severity, 'description': description})

        ext = os.path.splitext(fname)[1].lower()
        if ext not in ('.py', '.js', '.ts', '.tsx', '.jsx', '.go', '.rs', '.rb', '.sh', '.sql', '.yaml', '.yml', '.json', '.md', '.css', '.scss', '.html'):
            improvements.append(f'{fname}: non-standard extension, verify correctness manually')
        elif fdata['additions'] > 100:
            improvements.append(f'{fname}: {fdata["additions"]} lines added — consider splitting into smaller files')
        elif fdata['deletions'] > 50 and fdata['deletions'] > fdata['additions'] * 3:
            improvements.append(f'{fname}: mostly deletions ({fdata["deletions"]} removed) — verify nothing is accidentally removed')

    if not risks and total_additions < 200:
        confidence = 'High'
    elif len([r for r in risks if r['severity'] == 'high']) > 0:
        confidence = 'Low'
    elif len(risks) > 5:
        confidence = 'Low'
    elif len([r for r in risks if r['severity'] in ('high', 'medium')]) > 2:
        confidence = 'Medium'
    else:
        confidence = 'High'

    return risks, improvements, confidence, total_additions, total_deletions, changed_files

def generate_review(owner, repo, pr_number, pr_data, diff_text):
    files = analyze_diff(diff_text)
    risks, improvements, confidence, additions, deletions, changed = classify_changes(files)

    pr_title = pr_data.get('title', '')
    pr_body = (pr_data.get('body') or '')[:500]
    author = pr_data.get('user', {}).get('login', 'unknown')

    lines = []
    lines.append(f'## PR Review: [{owner}/{repo} #{pr_number}](https://github.com/{owner}/{repo}/pull/{pr_number})')
    lines.append('')
    lines.append(f'**{pr_title}** by @{author}')
    lines.append('')
    lines.append(f'### Summary')
    lines.append(f'{changed} file(s) changed — {additions} additions, {deletions} deletions.')
    body_summary = pr_body[:200].replace('\n', ' ').strip()
    if body_summary:
        lines.append(f'> {body_summary}')
    lines.append('')

    if risks:
        high = [r for r in risks if r['severity'] == 'high']
        medium = [r for r in risks if r['severity'] == 'medium']
        low = [r for r in risks if r['severity'] == 'low']

        lines.append(f'### Identified Risks ({len(risks)})')
        if high:
            lines.append(f'\n**High Severity ({len(high)})**')
            for r in high[:10]:
                lines.append(f'- ⚠️ {r["description"]} in `{r["file"]}`: `{r["line"]}`')
        if medium:
            lines.append(f'\n**Medium Severity ({len(medium)})**')
            for r in medium[:10]:
                lines.append(f'- ⚡ {r["description"]} in `{r["file"]}`: `{r["line"]}`')
        if low:
            lines.append(f'\n**Low Severity ({len(low)})**')
            for r in low[:5]:
                lines.append(f'- ℹ️ {r["description"]} in `{r["file"]}`: `{r["line"]}`')
        lines.append('')

    if improvements:
        lines.append(f'### Improvement Suggestions ({len(improvements)})')
        for imp in improvements[:10]:
            lines.append(f'- 💡 {imp}')
        lines.append('')

    lines.append(f'### Confidence Score: **{confidence}**')
    if confidence == 'High':
        lines.append('Changes are well-scoped with minimal risk. Ready for review.')
    elif confidence == 'Medium':
        lines.append('Some areas flagged — recommended to address medium-severity items before merging.')
    else:
        lines.append('Contains significant risks. Review each item before merging.')
    lines.append('')

    lines.append('---')
    lines.append(f'_Generated by claude-review agent | {changed} file(s), {additions}+{deletions}_')
    lines.append('')

    return '\n'.join(lines)

def main():
    parser = argparse.ArgumentParser(description='Review a GitHub PR')
    parser.add_argument('--pr', required=True, help='PR URL (https://github.com/owner/repo/pull/123)')
    args = parser.parse_args()

    owner, repo, pr_number = parse_pr_url(args.pr)

    pr_data = fetch(f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}')
    diff_text = fetch_diff(f'https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}')

    review = generate_review(owner, repo, pr_number, pr_data, diff_text)
    print(review)

if __name__ == '__main__':
    main()
