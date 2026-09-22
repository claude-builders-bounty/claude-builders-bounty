"""Install into the current user's Claude settings, preserving existing hooks."""
import json
from pathlib import Path
import shlex
import shutil
import sys


def install():
    folder = Path.home() / '.claude'
    settings_path = folder / 'settings.json'
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
    hooks = settings.setdefault('hooks', {}).setdefault('PreToolUse', [])
    if not isinstance(hooks, list):
        raise ValueError('PreToolUse must be an array; settings were not changed')
    target = folder / 'hooks' / 'destructive_guard.py'
    command = shlex.join([sys.executable.replace('\\', '/'), str(target).replace('\\', '/')])
    entry = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command, 'timeout': 5}]}
    if entry not in hooks:
        hooks.append(entry)
    target.parent.mkdir(parents=True, exist_ok=True)
    if settings_path.exists():
        # Exclusive backup creation prevents repeated installs overwriting it.
        try:
            with (folder / 'settings.before-destructive-guard.json').open('xb') as backup:
                backup.write(settings_path.read_bytes())
        except FileExistsError:
            pass
    shutil.copyfile(Path(__file__).with_name('guard.py'), target)
    temporary = folder / 'settings.destructive-guard.tmp'
    with temporary.open('x', encoding='utf-8') as output:
        output.write(json.dumps(settings, indent=2) + '\n')
    temporary.replace(settings_path)
    print('Installed Bash PreToolUse hook. Restart Claude Code and verify it in /hooks.')


if __name__ == '__main__':
    install()
