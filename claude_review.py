#!/usr/bin/env python3
import argparse
import subprocess


def sh(args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)


def changed_files(diff):
    files = []
    for line in diff.splitlines():
        if not line.startswith('diff --git a/'):
            continue
        rest = line[len('diff --git a/'):]
        _, sep, right = rest.partition(' b/')
        files.append(right if sep else rest)
    return files


def analyze(diff):
    files = changed_files(diff)
    risks = []
    if any('package-lock' in f or 'pnpm-lock' in f for f in files):
        risks.append('Dependency lockfile changed; review dependency intent.')
    if any('/api/' in f or 'server' in f.lower() for f in files):
        risks.append('Server/API code changed; verify auth, validation, and error handling.')
    if not risks:
        risks.append('No obvious high-risk file patterns detected from the changed paths.')

    suggestions = [
        'Add or update tests for changed behavior.',
        'Keep the PR focused and document any migration or config changes.',
    ]
    if len(diff) > 10000:
        confidence = 'High'
    elif len(diff) > 2000:
        confidence = 'Medium'
    else:
        confidence = 'Low'

    summary = (
        f'This PR changes {len(files)} file(s). '
        'The review uses changed paths and diff size to flag common integration, dependency, and safety risks.'
    )
    return '\n'.join(
        ['## PR Review', '', '### Summary', summary, '', '### Identified risks']
        + [f'- {risk}' for risk in risks]
        + ['', '### Improvement suggestions']
        + [f'- {suggestion}' for suggestion in suggestions]
        + ['', f'### Confidence: {confidence}', '']
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pr', required=True)
    args = parser.parse_args()
    diff = sh(['gh', 'pr', 'diff', args.pr])
    print(analyze(diff))


if __name__ == '__main__':
    main()
