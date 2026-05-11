# block-destructive.sh — Claude Code PreToolUse Hook

Blocks dangerous bash commands before Claude Code executes them.
Keeps your projects (and your nerves) intact.

## 2-Command Install

```bash
mkdir -p ~/.claude/hooks && curl -L https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive.sh -o ~/.claude/hooks/block-destructive.sh && chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add to `~/.claude/settings.json` (or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Why | Safer Alternative |
|---------|-----|-------------------|
| `rm -rf` / `rm -fr` | Recursive force delete — gone forever | `trash`, `rm -i`, or `git clean -fdx --dry-run` first |
| `DROP TABLE` | Permanently destroys a database table | Backup first, then drop |
| `git push --force` / `git push -f` | Rewrites remote history for everyone | `git push --force-with-lease` |
| `TRUNCATE` | Removes all rows instantly, irreversibly | `DELETE` with WHERE clause |
| `DELETE FROM` (no WHERE) | Deletes ALL rows — oops | Always add a WHERE clause |

## How It Works

1. Hook fires on every `Bash` tool call via Claude Code's `PreToolUse` event
2. Parses the command from the hook's stdin JSON
3. Checks against blocked patterns (case-insensitive)
4. If blocked:
   - Logs to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
   - Returns a structured `block` decision so Claude explains *why* it can't run the command
   - Exits with code 2 (hook convention for "block this action")
5. If clean: exits with code 0, command runs normally

## Log Format

```
[2026-05-11T12:00:00Z] Blocked: 'rm -rf' is a destructive recursive delete... | Command: rm -rf /tmp/build | Project: /Users/you/my-project
```

View your log: `cat ~/.claude/hooks/blocked.log`

## Files

| File | Purpose |
|------|---------|
| `hooks/block-destructive.sh` | The hook script |
| `settings-example.json` | Drop-in `~/.claude/settings.json` config |
| `README-block-destructive.md` | This documentation |
