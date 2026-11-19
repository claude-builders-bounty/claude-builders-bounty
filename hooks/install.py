"""Install the hook and register it without replacing unrelated settings."""
import json
from pathlib import Path
import shlex
import shutil
import sys


def install(root=None):
    root = Path(root) if root is not None else Path.home() / '.claude'
    target = root / 'hooks' / 'pre-tool-use.py'
    target.parent.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).with_name('pre-tool-use.py')
    if source.resolve() != target.resolve():
        shutil.copyfile(source, target)
    settings_path = root / 'settings.json'
    settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}
    command = f'{shlex.quote(sys.executable)} {shlex.quote(str(target))}'
    registration = {'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': command}]}
    hooks = settings.setdefault('hooks', {}).setdefault('PreToolUse', [])
    if registration not in hooks:
        hooks.append(registration)
    settings_path.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    install()
