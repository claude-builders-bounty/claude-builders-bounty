#!/usr/bin/env python3
"""Install the hook, preserving existing Claude settings and hook entries."""
import json
import pathlib
import shlex
import shutil

root = pathlib.Path.home() / '.claude'
settings_path = root / 'settings.json'
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
source = pathlib.Path(__file__).parent / 'pre_tool_use.py'
target = root / 'hooks/katarina_pre_tool_use.py'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)
command = 'python3 ' + shlex.quote(str(target))
entries = settings.setdefault('hooks', {}).setdefault('PreToolUse', [])
if not any(hook.get('command') == command for entry in entries for hook in entry.get('hooks', [])):
    entries.append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]})
if settings_path.exists():
    shutil.copyfile(settings_path, settings_path.with_suffix('.json.katarina-backup'))
settings_path.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
print('Installed. Restart Claude Code. Existing hooks and settings were preserved.')
