"""Install into the selected home without clobbering other hook settings."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def install(home):
    root = Path(home) / '.claude'
    settings = root / 'settings.json'
    data = json.loads(settings.read_text(encoding='utf-8')) if settings.exists() else {}
    if not isinstance(data, dict):
        raise ValueError('settings must be a JSON object')
    hooks = data.setdefault('hooks', {})
    groups = hooks.setdefault('PreToolUse', [])
    if not isinstance(groups, list):
        raise ValueError('PreToolUse must be a list')
    dest = root / 'hooks' / 'destructive_command_guard.py'
    # Current Claude Code supports command + args, avoiding shell path quoting.
    entry = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': sys.executable,
             'args': [str(dest)], 'timeout': 10}]}
    if entry not in groups:
        groups.append(entry)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.read_bytes() != Path(__file__).with_name('guard.py').read_bytes():
        raise ValueError('existing guard differs; back it up and remove it before upgrading')
    shutil.copyfile(Path(__file__).with_name('guard.py'), dest)
    if settings.exists():
        backup = settings.with_name('settings.json.before-destructive-guard')
        if not backup.exists():
            shutil.copyfile(settings, backup)
    fd, temp = tempfile.mkstemp(prefix='settings-', suffix='.json', dir=root)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, indent=2)
            stream.write('\n')
        os.replace(temp, settings)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return dest


if __name__ == '__main__':
    print('Installed:', install(Path.home()))
