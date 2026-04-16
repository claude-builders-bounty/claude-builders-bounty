# Destructive Command Blocker — Claude Code Hook

A `pre-tool-use` hook that intercepts dangerous bash commands before Claude Code executes them.

## Setup (2 steps)

1. Copy the hook:
   ```bash
   mkdir -p ~/.claude/hooks && cp hooks/block-destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.py
   ```

2. Register in `~/.claude/settings.json`:
   ```bash
   python3 -c "
   import json
   from pathlib import Path
   p = Path.home() / '.claude' / 'settings.json'
   s = json.loads(p.read_text()) if p.exists() else {}
   h = s.get('hooks', {}).get('PreToolUse', [])
   entry = {'command': str(Path.home() / '.claude' / 'hooks' / 'block-destructive.py')}
   if entry not in h: h.append(entry)
   s.setdefault('hooks', {})['PreToolUse'] = h
   p.write_text(json.dumps(s, indent=2))
   print('✅ Done')
   "
   ```

Or run `bash hooks/install.sh` to do both steps automatically.

## What it blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -fr` | Recursive force-delete |
| `DROP TABLE` | Permanent table deletion |
| `git push --force` / `-f` | Overwrites remote history |
| `TRUNCATE` | Removes all table rows |
| `DELETE FROM` (no WHERE) | Deletes all matching rows |

## How it works

1. Reads tool call JSON from stdin
2. Checks Bash commands against blocked patterns
3. If blocked: logs to `~/.claude/hooks/blocked.log` and returns `"decision": "block"` with explanation
4. If safe: outputs nothing (approval)

## Blocked log format

```
[2026-04-16T10:30:00] BLOCKED: rm -rf: recursively force-delete files/directories
  Command: rm -rf /important-data
  Project: /home/user/project
```

## Requirements

- Python 3.10+ (for `str | None` type hint; or change to `Optional[str]`)
- Claude Code with hooks support
