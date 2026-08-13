# Destructive Bash Command Guard for Claude Code

This hook blocks high-risk Bash commands before Claude Code runs them.

It implements a Claude Code `PreToolUse` hook for the Bash tool and blocks:

- Recursive + force file removal, including compact and long-form variants:
  - `rm -rf path`
  - `rm -fr path`
  - `rm --recursive --force path`
  - `rm --force --recursive path`
- `DROP TABLE`
- `git push --force` / `git push -f` / `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

with timestamp, attempted command, and project path.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/destructive_command_guard.py ~/.claude/hooks/destructive_command_guard.py && chmod +x ~/.claude/hooks/destructive_command_guard.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
try:
    data = json.loads(p.read_text())
except Exception:
    data = {}
hooks = data.setdefault('hooks', {})
pre = hooks.setdefault('PreToolUse', [])
entry = {
    'matcher': 'Bash',
    'hooks': [{
        'type': 'command',
        'command': str(pathlib.Path.home() / '.claude' / 'hooks' / 'destructive_command_guard.py')
    }]
}
if entry not in pre:
    pre.append(entry)
p.write_text(json.dumps(data, indent=2) + '\n')
print(p)
PY
```

## Quick local test

Allowed command:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"git status"},"cwd":"/tmp"}' \
  | python3 .claude/hooks/destructive_command_guard.py
```

Blocked command:

```bash
printf '%s\n' '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | python3 .claude/hooks/destructive_command_guard.py
```

The blocked command exits with status `2` and writes a line to `~/.claude/hooks/blocked.log`.
