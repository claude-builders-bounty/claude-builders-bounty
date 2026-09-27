"""Integration test for AUTOMATON-CHANGELOG-SOLUTION.py using real Git."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOLUTION = ROOT / 'AUTOMATON-CHANGELOG-SOLUTION.py'
PUBLIC = ROOT / 'public-repo'
REPORT = ROOT / 'REAL-GIT-TEST-RESULT.json'
PREFIX = re.compile(r'^(?:feat|feature|add|fix|bug|change|refactor|perf|remove|delete)(?:\([^)]*\))?!?:\s*', re.I)

def run(*args, cwd, env=None):
    return subprocess.run(args, cwd=cwd, env=env, check=True, text=True, capture_output=True).stdout.strip()

def git(repo, *args):
    return run('git', *args, cwd=repo)

def generate(repo):
    run(sys.executable, str(SOLUTION), cwd=repo)
    return (repo / 'CHANGELOG.md').read_text(encoding='utf-8')

def expected_records(repo, baseline=None):
    spec = [f'{baseline}..HEAD'] if baseline else []
    raw = git(repo, 'log', *spec, '--date=short', '--pretty=format:%h%x1f%s%x1f%ad%x1e')
    return [tuple(r.strip().split('\x1f')) for r in raw.split('\x1e') if r.strip()]

def verify_entries(output, records):
    entries = re.findall(r'^- (.*?) \(([0-9a-f]+), (\d{4}-\d{2}-\d{2})\)$', output, re.M)
    assert len(entries) == len(records), f'entry count: {len(entries)} != {len(records)}'
    expected = [(PREFIX.sub('', subject), sha, date) for sha, subject, date in records]
    assert sorted(entries) == sorted(expected), f'Changelog entries differ from git log: {entries!r} != {expected!r}'
    assert '### Changed' in output or any('### ' + category in output for category in ('Added', 'Fixed', 'Removed'))

def local_repo(folder, with_tag):
    repo = folder / ('tagged' if with_tag else 'untagged')
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'Automaton Test')
    git(repo, 'config', 'user.email', 'automaton@example.invalid')
    def commit(subject, stamp):
        env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)
        run('git', 'commit', '-q', '--allow-empty', '-m', subject, cwd=repo, env=env)
        return git(repo, 'rev-parse', 'HEAD')
    first = commit('feat: Before baseline' if with_tag else 'feat: Initial feature', '2024-01-01T12:00:00+00:00')
    if with_tag:
        git(repo, 'tag', 'v1.0', first)
        commit('fix: After baseline', '2024-01-02T12:00:00+00:00')
        baseline = 'v1.0'
    else:
        commit('remove: Old setting', '2024-01-02T12:00:00+00:00')
        baseline = None
    output = generate(repo)
    records = expected_records(repo, baseline)
    verify_entries(output, records)
    assert ('## Changes since v1.0' in output) == with_tag
    if with_tag:
        assert 'After baseline' in output and 'Before baseline' not in output
        assert '### Fixed' in output
    else:
        assert 'Initial feature' in output and 'Old setting' in output
        assert '### Added' in output and '### Removed' in output
    return {'result': 'PASS', 'head': git(repo, 'rev-parse', 'HEAD'), 'baseline': baseline, 'git_log_commits': len(records), 'checks': ['real Git history', 'entry equality after documented prefix removal', 'tag boundary' if with_tag else 'history without tags', 'category heading']}

def main():
    assert (PUBLIC / '.git').exists(), 'Broker did not provide real Git checkout'
    head = git(PUBLIC, 'rev-parse', 'HEAD')
    try:
        baseline = git(PUBLIC, 'describe', '--tags', '--abbrev=0')
    except subprocess.CalledProcessError:
        baseline = None
    output = generate(PUBLIC)
    records = expected_records(PUBLIC, baseline)
    verify_entries(output, records)
    assert ('## Changes since ' + baseline in output) if baseline else ('## Changes\n' in output)
    with tempfile.TemporaryDirectory() as name:
        folder = Path(name)
        tagged = local_repo(folder, True)
        untagged = local_repo(folder, False)
    report = {'result': 'PASS', 'public_source': 'https://github.com/octocat/Hello-World', 'public_head_commit': head, 'public_baseline': baseline, 'public_git_log_commits': len(records), 'public_checks': ['real .git checkout', 'generated CHANGELOG.md', 'every changelog entry matches git log subject after prefix removal, short hash, and author date', 'entry count equals git log'], 'tagged_local_repository': tagged, 'untagged_local_repository': untagged, 'note': 'The broker response independently reports fetched commit and shallow status; if shallow, the public history is limited to fetched commits (at most 100).'}
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
