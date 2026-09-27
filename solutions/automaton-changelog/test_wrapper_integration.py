import json
import shutil
import subprocess
from pathlib import Path

root = Path('public-repo').resolve()
wrapper = root / 'changelog.sh'
generator = root / 'AUTOMATON-CHANGELOG-SOLUTION.py'
shutil.copyfile('submission/changelog.sh', wrapper)
shutil.copyfile('AUTOMATON-CHANGELOG-SOLUTION.py', generator)

def git(*args):
    return subprocess.run(['git', *args], cwd=root, text=True, capture_output=True, check=True).stdout.strip()

commit = git('rev-parse', 'HEAD')
command = ['bash', 'changelog.sh']
run = subprocess.run(command, cwd=root, text=True, capture_output=True)
output = root / 'CHANGELOG.md'
assertions = {}
assertions['exit_zero'] = run.returncode == 0
assertions['output_in_caller_cwd'] = output.is_file()
assertions['no_output_at_wrapper_source'] = not Path('submission/CHANGELOG.md').exists()
if output.is_file():
    body = output.read_text(encoding='utf-8')
    history = git('log', '--date=short', '--pretty=format:%h%x1f%s%x1f%ad%x1e')
    records = [record.strip().split('\x1f') for record in history.split('\x1e') if record.strip()]
    assertions['one_entry_per_real_commit'] = sum(body.count(' (' + h + ', ' + d + ')') for h, _s, d in records) == len(records)
    assertions['actual_subjects_and_dates'] = all(s in body and (' (' + h + ', ' + d + ')') in body for h, s, d in records)
    assertions['changelog_header'] = body.startswith('# Changelog\n')
else:
    assertions['one_entry_per_real_commit'] = False
    assertions['actual_subjects_and_dates'] = False
    assertions['changelog_header'] = False
result = {'repository_commit': commit, 'command': command, 'exit_status': run.returncode, 'stdout': run.stdout, 'stderr': run.stderr, 'assertions': assertions}
Path('REAL-GIT-WRAPPER-RESULT.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
assert all(assertions.values()), result
