#!/usr/bin/env python3
"""Install the Bash guard without replacing unrelated Claude settings."""
import copy
import json
from pathlib import Path
import shlex
import shutil
import sys

def updated_settings(settings, command):
    settings = copy.deepcopy(settings)
    if not isinstance(settings, dict): raise ValueError('settings root must be an object')
    hooks = settings.setdefault('hooks', {})
    if not isinstance(hooks, dict): raise ValueError('hooks must be an object')
    pre = hooks.setdefault('PreToolUse', [])
    if not isinstance(pre, list): raise ValueError('PreToolUse must be an array')
    for group in pre:
        if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
            raise ValueError('invalid PreToolUse group; refusing to overwrite settings')
        for handler in group['hooks']:
            if not isinstance(handler, dict): raise ValueError('invalid hook handler')
            if group.get('matcher') == 'Bash' and handler.get('command') == command:
                return settings
    pre.append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]})
    return settings

def main():
    source = Path(__file__).with_name('block-destructive.py')
    if not source.is_file(): raise ValueError('block-destructive.py is missing')
    settings_path = Path.home() / '.claude' / 'settings.json'
    original = settings_path.read_text(encoding='utf-8') if settings_path.exists() else None
    settings = json.loads(original) if original is not None else {}
    target = settings_path.parent / 'hooks' / source.name
    command = shlex.quote(Path(sys.executable).as_posix()) + ' ' + shlex.quote(target.as_posix())
    updated = updated_settings(settings, command)
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != target.resolve(): shutil.copyfile(source, target)
    target.chmod(0o700)
    backup = settings_path.with_name('settings.json.before-destructive-guard.bak')
    if original is not None and not backup.exists():
        backup.write_text(original, encoding='utf-8')
        backup.chmod(0o600)
    temporary = settings_path.with_name('settings.json.destructive-guard.tmp')
    with temporary.open('x', encoding='utf-8') as handle:
        handle.write(json.dumps(updated, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(settings_path)
    print('Installed guard; unrelated settings preserved. Restart Claude Code to load hooks.')
    return 0

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError) as error: raise SystemExit(str(error))
