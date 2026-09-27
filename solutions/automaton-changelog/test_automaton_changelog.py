import importlib.util
import os
import subprocess
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location('changelog', 'AUTOMATON-CHANGELOG-SOLUTION.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
original_git = mod.git
original_cwd = Path.cwd()

def check(fake, expected, code=0):
    with tempfile.TemporaryDirectory() as folder:
        os.chdir(folder)
        try:
            mod.git = fake
            result = mod.generate()
            assert result == code, (result, code)
            if expected is not None:
                text = Path('CHANGELOG.md').read_text(encoding='utf-8')
                for fragment in expected:
                    assert fragment in text, (fragment, text)
            else:
                assert not Path('CHANGELOG.md').exists()
        finally:
            os.chdir(original_cwd)
            mod.git = original_git

def tagged(*args):
    if args[0] == 'describe':
        return 'v1.0'
    if args[0] == 'log':
        assert args[1] == 'v1.0..HEAD', args
        return 'a1\x1ffeat(api): Export CSV\x1f2026-09-01\x1eb2\x1ffix: Escape cell\x1f2026-09-02\x1ec3\x1frefactor: Stream rows\x1f2026-09-03\x1ed4\x1fremove: Old flag\x1f2026-09-04\x1ee5\x1fUpdate docs\x1f2026-09-05\x1e'
    return 'true'
check(tagged, ['Changes since v1.0', '### Added', 'Export CSV', '### Fixed', 'Escape cell', '### Changed', 'Stream rows', 'Update docs', '### Removed', 'Old flag'])

def untagged(*args):
    if args[0] == 'describe':
        raise subprocess.CalledProcessError(128, args)
    if args[0] == 'log':
        assert not any('..HEAD' in item for item in args), args
        return 'a1\x1ffeat: First feature\x1f2026-09-01\x1e'
    return 'true'
check(untagged, ['## Changes', 'First feature'])

def empty(*args):
    return 'v1.0' if args[0] == 'describe' else ''
check(empty, ['No commits found since the selected baseline.'])

def broken(*args):
    raise FileNotFoundError('git')
check(broken, None, 2)
print('PASS: tagged categories, tagless history, empty history, missing Git')
