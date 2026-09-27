"""Check changelog output against public commit metadata from octocat/Hello-World.

Source: https://api.github.com/repos/octocat/Hello-World/commits?per_page=2
Fetched 2026-09-25. The isolated runner cannot clone Git repositories; this test
feeds the published commit metadata through the generator's Git adapter.
"""
import importlib.util
import os
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('changelog', 'AUTOMATON-CHANGELOG-SOLUTION.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# These records are from the public GitHub API response, using each commit's
# SHA, first message line, and committer date. No tag is assumed.
records = [
    ('7fd1a60', 'Merge pull request #6 from Spaceghost/patch-1', '2012-03-06'),
    ('7629413', 'New line at end of file. --Signed off by Spaceghost', '2011-09-14'),
]
git_log = ''.join('\x1f'.join(record) + '\x1e' for record in records)

def public_history(*args):
    if args[0] == 'rev-parse':
        return 'true'
    if args[0] == 'describe':
        import subprocess
        raise subprocess.CalledProcessError(128, args)
    if args[0] == 'log':
        assert not any('..HEAD' in arg for arg in args), args
        return git_log
    raise AssertionError(args)

mod.git = public_history
with tempfile.TemporaryDirectory() as directory:
    os.chdir(directory)
    assert mod.generate() == 0
    result = Path('CHANGELOG.md').read_text(encoding='utf-8')
    assert '## Changes\n' in result
    assert '### Changed\n' in result
    assert '- Merge pull request #6 from Spaceghost/patch-1 (7fd1a60, 2012-03-06)' in result
    assert '- New line at end of file. --Signed off by Spaceghost (7629413, 2011-09-14)' in result
    assert result.count('\n- ') == 2
    print(result)
print('PASS: published GitHub commit sample')
