# Destructive Bash PreToolUse Hook

Claude Code `PreToolUse` hook for issue #3. It blocks destructive Bash commands before Claude Code can run them and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(p.read_text() if p.exists() else '{}')
settings.setdefault('hooks', {})['PreToolUse'] = [{
  'matcher': 'Bash',
  'hooks': [{'type': 'command', 'command': 'python3 ~/.claude/hooks/block_destructive_bash.py'}]
}]
p.write_text(json.dumps(settings, indent=2) + '\n')
PY
```

Alternatively, copy `hooks/settings.example.json` into your Claude Code settings and adjust the path if needed.

## What it blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause before the next semicolon/newline

Safe commands exit with no output so Claude Code proceeds normally.

## Claude Code hook behavior

The hook reads the standard Claude Code `PreToolUse` JSON from stdin. For dangerous Bash commands it returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive Bash command blocked by PreToolUse hook (...)"
  }
}
```

## Log format

Every blocked command appends one JSON line to `~/.claude/hooks/blocked.log` with:

- `timestamp`
- `project_path`
- `command`
- `rule_id`
- `reason`

Example:

```json
{"timestamp":"2026-05-13T00:00:00+00:00","project_path":"/repo","command":"rm -rf build","rule_id":"rm-rf","reason":"rm -rf / rm -fr recursively deletes files without confirmation"}
```

## Local test

```bash
python3 -m unittest discover -s tests -v
```
