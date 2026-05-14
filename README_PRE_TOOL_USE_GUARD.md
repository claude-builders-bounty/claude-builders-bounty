# Claude Code PreToolUse Bash Safety Guard

A small defensive Claude Code hook that blocks high-risk Bash commands before they run.

It is intentionally dependency-free, testable, and narrow: normal commands pass through, but commands that can erase data or rewrite shared history are stopped with a clear message and an audit log entry.

## Install in 2 commands

From this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_guard.py ~/.claude/hooks/pre_tool_use_guard.py && chmod +x ~/.claude/hooks/pre_tool_use_guard.py
python3 - <<'PY'
import json
from pathlib import Path
settings = Path.home() / '.claude' / 'settings.json'
settings.parent.mkdir(parents=True, exist_ok=True)
data = json.loads(settings.read_text()) if settings.exists() else {}
data.setdefault('hooks', {}).setdefault('PreToolUse', []).append({
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/pre_tool_use_guard.py'}],
})
settings.write_text(json.dumps(data, indent=2) + '\n')
PY
```

## What gets blocked

- `rm -rf` style recursive forced removal
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, or `git push -f`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to:

```text
~/.claude/hooks/blocked.log
```

Each line is JSON with:

- `timestamp`
- `rule`
- `command`
- `project_path`

## Behavior

When a command is blocked, the hook:

1. Logs the attempt.
2. Prints a clear explanation for Claude.
3. Exits with code `2`, which Claude Code treats as a blocking hook failure for `PreToolUse`.

Allowed commands exit `0` and do not interfere with normal work.

## Manual test

```bash
printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main","cwd":"/tmp/demo"}}' \
  | python3 hooks/pre_tool_use_guard.py
```

Expected result: exit code `2`, a block message on stderr, and a new JSON line in `~/.claude/hooks/blocked.log`.

Run the automated tests:

```bash
python3 -m unittest discover -v
```
