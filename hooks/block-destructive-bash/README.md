# Block destructive Bash commands (Claude Code PreToolUse hook)

A `PreToolUse` hook for Claude Code that denies obviously destructive shell commands before they execute.

## What it blocks

- `rm -rf` (including `rm -fr`)
- `git push --force` (including `-f`)
- SQL-like destructive patterns inside shell commands:
  - `DROP TABLE`
  - `TRUNCATE`
  - `DELETE FROM` (only when there is **no** `WHERE` after it)

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as a JSONL line containing:
- `ts` (UTC timestamp)
- `project_dir`
- `rule`
- `command`

## Install (2 commands)

1) Install the hook script:

```bash
mkdir -p ~/.claude/hooks \
  && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-bash/block_destructive_bash.py \
    -o ~/.claude/hooks/block_destructive_bash.py \
  && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

2) Register the hook in `~/.claude/settings.json`:

```bash
python3 - <<'PY'
import json
import os
from pathlib import Path

settings_path = Path(os.path.expanduser('~/.claude/settings.json'))
settings_path.parent.mkdir(parents=True, exist_ok=True)

if settings_path.exists():
    data = json.loads(settings_path.read_text(encoding='utf-8') or '{}')
else:
    data = {}

hooks = data.setdefault('hooks', {})
pre = hooks.setdefault('PreToolUse', [])

# Idempotency: don't add if already present
for entry in pre:
    for h in (entry.get('hooks') or []):
        cmd = h.get('command')
        if isinstance(cmd, str) and 'block_destructive_bash.py' in cmd:
            settings_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
            raise SystemExit(0)

pre.append({
    'matcher': 'Bash',
    'hooks': [
        {
            'type': 'command',
            'command': 'python3 ~/.claude/hooks/block_destructive_bash.py',
        }
    ],
})

settings_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
print(f'Updated {settings_path}')
PY
```

## Notes

- This hook only runs for the `Bash` tool (`matcher: "Bash"`).
- Normal commands are unaffected.
- If you want to debug hooks, see the official docs and run Claude Code with `--debug`.
