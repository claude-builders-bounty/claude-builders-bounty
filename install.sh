#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "$0")" && pwd)"
python3 - "$ROOT/hooks/block-destructive-bash.py" <<'PY'
import json
import os
from pathlib import Path
import shutil
import sys

source = Path(sys.argv[1])
target = Path.home() / '.claude' / 'hooks' / 'block-destructive-bash.py'
settings = Path.home() / '.claude' / 'settings.json'
target.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(source, target)
target.chmod(0o755)
settings.parent.mkdir(parents=True, exist_ok=True)
if settings.exists():
    content = json.loads(settings.read_text(encoding='utf-8'))
    if not isinstance(content, dict):
        raise ValueError('Claude settings.json must be a JSON object')
else:
    content = {}
hooks = content.setdefault('hooks', {})
if not isinstance(hooks, dict):
    raise ValueError('Claude settings hooks must be a JSON object')
pre = hooks.setdefault('PreToolUse', [])
if not isinstance(pre, list):
    raise ValueError('Claude PreToolUse must be a list')
command = str(target)
if not any(isinstance(rule, dict) and any(isinstance(h, dict) and h.get('command') == command for h in rule.get('hooks', [])) for rule in pre):
    pre.append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]})
tmp = settings.with_name(settings.name + '.tmp')
tmp.write_text(json.dumps(content, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
os.replace(tmp, settings)
print(f'Installed {target} and registered Bash PreToolUse hook in {settings}')
PY
