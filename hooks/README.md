# Destructive Bash Blocker for Claude Code

A Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended as JSONL to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes a UTC timestamp, attempted command, project path, and block reason.

## Install in 2 commands

From this repository:

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
path = pathlib.Path.home() / '.claude' / 'settings.json'
settings = json.loads(path.read_text()) if path.exists() else {}
settings.setdefault('hooks', {}).setdefault('PreToolUse', []).append({
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': str(pathlib.Path.home() / '.claude' / 'hooks' / 'block_destructive_bash.py')}]
})
path.write_text(json.dumps(settings, indent=2) + '\n')
print(f'Installed Claude Code PreToolUse hook in {path}')
PY
```

Restart Claude Code after installing so it reloads hook settings.

## How it works

Claude Code sends hook event JSON to command hooks on stdin. This script reads the `PreToolUse` payload, checks Bash tool input for destructive patterns, logs blocked attempts, and returns a `permissionDecision: deny` response with a clear explanation for Claude.

Normal Bash commands exit successfully with no output, so the hook does not interfere with day-to-day use.

## Manual smoke test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/build"},"cwd":"/tmp/project"}' \
  | python3 hooks/block_destructive_bash.py
```

Expected output includes:

```json
{"permissionDecision":"deny"}
```

Then inspect:

```bash
tail -n 1 ~/.claude/hooks/blocked.log
```
