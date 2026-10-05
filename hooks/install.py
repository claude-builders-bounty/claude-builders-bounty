#!/usr/bin/env python3
"""Install only when explicitly run; preserve all other Claude user settings."""
import json
from pathlib import Path
import shlex
import sys


def install(home):
    directory = home / '.claude' / 'hooks'
    target = directory / 'block_destructive.py'
    settings_path = home / '.claude' / 'settings.json'
    source = Path(__file__).with_name('block_destructive.py').read_bytes()
    settings = json.loads(settings_path.read_text(encoding='utf-8')) if settings_path.exists() else {}
    if not isinstance(settings, dict):
        raise ValueError('settings.json must contain an object')
    hooks = settings.setdefault('hooks', {}).setdefault('PreToolUse', [])
    if not isinstance(hooks, list):
        raise ValueError('PreToolUse settings must be an array')
    entry = {'matcher': 'Bash', 'hooks': [{'type': 'command',
             'command': shlex.quote(sys.executable) + ' ' + shlex.quote(str(target)), 'timeout': 5}]}
    if target.exists() and target.read_bytes() != source:
        raise ValueError('existing block_destructive.py differs; review it before replacing it')
    if entry not in hooks:
        hooks.append(entry)
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target.write_bytes(source)
    target.chmod(0o700)
    # Preserve an exact pre-install copy; validate the settings before any writes.
    backup = settings_path.with_suffix('.json.before-destructive-hook')
    if settings_path.exists() and not backup.exists():
        backup.write_bytes(settings_path.read_bytes())
        backup.chmod(0o600)
    temporary = settings_path.with_suffix('.json.destructive-hook.tmp')
    temporary.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
    temporary.chmod(0o600)
    temporary.replace(settings_path)
    return target


if __name__ == '__main__':
    try:
        print('Installed: ' + str(install(Path.home())))
    except (OSError, ValueError, TypeError, AttributeError) as error:
        print('Installation stopped: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
