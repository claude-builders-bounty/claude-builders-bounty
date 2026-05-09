# Destructive Bash Guard for Claude Code

A Claude Code `PreToolUse` hook that blocks common destructive Bash commands before they run.

## What it blocks

- `rm -rf` / `rm -fr` style recursive force deletion
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, reason, and project path.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 - <<'PY'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
p.parent.mkdir(parents=True, exist_ok=True)
config = json.loads(p.read_text()) if p.exists() else {}
config.setdefault('hooks', {}).setdefault('PreToolUse', []).append({
    'matcher': 'Bash',
    'hooks': [{'type': 'command', 'command': '$HOME/.claude/hooks/block_destructive_bash.py'}]
})
p.write_text(json.dumps(config, indent=2) + '\n')
PY
```

Alternatively, merge `settings.example.json` into your Claude Code settings manually.

## How it works

Claude Code sends hook event JSON on stdin before each Bash tool call. For dangerous commands, this hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: ..."
  }
}
```

For normal commands, it exits successfully with no output, so it does not interfere.

## Test locally

```bash
python3 tests/test_block_destructive_bash.py
```
