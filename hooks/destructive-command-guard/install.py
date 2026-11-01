#!/usr/bin/env python3
"""Explicit local install only. Does not run during review or tests outside isolated HOME."""
import json, os, shutil
from datetime import datetime, timezone
from pathlib import Path

def main():
    home = Path.home() / '.claude'
    settings = home / 'settings.json'
    data = json.loads(settings.read_text()) if settings.exists() else {}
    if not isinstance(data, dict): raise ValueError('settings must be an object')
    hooks = data.setdefault('hooks', {})
    if not isinstance(hooks, dict): raise ValueError('hooks must be an object')
    groups = hooks.setdefault('PreToolUse', [])
    if not isinstance(groups, list): raise ValueError('PreToolUse must be a list')
    target = home / 'hooks/pre_tool_use_hook.py'
    command = 'python3 ' + __import__('shlex').quote(str(target))
    already = any(isinstance(g,dict) and g.get('matcher') == 'Bash' and any(isinstance(h,dict) and h.get('command') == command for h in g.get('hooks',[])) for g in groups)
    if not already: groups.append({'matcher':'Bash','hooks':[{'type':'command','command':command}]})
    target.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if settings.exists(): shutil.copy2(settings, home / ('settings.json.backup.' + stamp))
    if target.exists(): shutil.copy2(target, target.with_name(target.name+'.backup.'+stamp))
    shutil.copy2(Path(__file__).with_name('pre_tool_use_hook.py'), target)
    temp = settings.with_name('settings.json.narin-install.'+str(os.getpid()))
    with temp.open('x', encoding='utf-8') as f: f.write(json.dumps(data, indent=2)+'\n')
    os.replace(temp, settings)
    print('Installed; existing settings preserved and backed up. Restart Claude Code to load hooks.')
if __name__ == '__main__': main()
