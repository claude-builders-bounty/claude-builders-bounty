#!/usr/bin/env python3
import argparse
import json
import subprocess
import urllib.parse


def fetch_pr(url: str):
    parts = urllib.parse.urlparse(url).path.strip('/').split('/')
    if len(parts) < 4 or parts[2] != 'pull':
        raise SystemExit('invalid PR URL')
    repo = f'{parts[0]}/{parts[1]}'
    number = parts[3]
    meta = json.loads(subprocess.check_output([
        'gh', 'pr', 'view', number, '--repo', repo,
        '--json', 'title,files,additions,deletions'
    ], text=True))
    diff = subprocess.check_output(['gh', 'pr', 'diff', number, '--repo', repo], text=True)
    return meta, diff


def review(meta, diff: str) -> str:
    low = diff.lower()
    risks = []
    suggestions = []

    if any(token in low for token in ['api_key', 'password', 'secret']):
        risks.append('Potential credential-sensitive change; verify no secret is committed.')
    if any(token in low for token in ['subprocess', 'exec(', 'eval(']):
        risks.append('Execution surface changed; validate inputs and failure handling.')
    if meta.get('additions', 0) + meta.get('deletions', 0) > 800:
        risks.append('Large diff increases review risk; consider splitting if practical.')
    if 'test' not in low and 'spec' not in low:
        suggestions.append('Add or update tests for the changed behavior.')
    if not risks:
        risks.append('No high-signal deterministic risk found; semantic review is still recommended.')
    if not suggestions:
        suggestions.append('Confirm edge cases, error paths, and backward compatibility.')

    summary = (
        f"{meta.get('title', 'PR')} changes {len(meta.get('files', []))} file(s), "
        f"+{meta.get('additions', 0)}/-{meta.get('deletions', 0)}. "
        "The review below highlights deterministic risk signals from the diff."
    )

    sections = [
        '## Summary', summary, '',
        '## Identified risks', *[f'- {x}' for x in risks], '',
        '## Improvement suggestions', *[f'- {x}' for x in suggestions], '',
        '## Confidence', 'Medium', ''
    ]
    return '\n'.join(sections)


def main():
    parser = argparse.ArgumentParser(description='Review a GitHub pull request and emit structured Markdown.')
    parser.add_argument('--pr', required=True, help='GitHub pull request URL')
    args = parser.parse_args()
    meta, diff = fetch_pr(args.pr)
    print(review(meta, diff))


if __name__ == '__main__':
    main()
