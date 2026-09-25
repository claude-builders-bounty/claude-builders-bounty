# block-destructive — a Claude Code PreToolUse safety hook

Blocks destructive Bash commands before Claude Code executes them:
`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM`
without a `WHERE` clause. Every blocked attempt is logged to
`~/.claude/hooks/blocked.log` with a timestamp, the attempted command, and the
project path.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
```

Then register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "~/.claude/hooks/block_destructive.py" }
        ]
      }
    ]
  }
}
```

## Behavior

- Intercepts `PreToolUse` events for the `Bash` tool only; every other tool is
  passed through untouched.
- Outputs `{"decision": "block", "reason": "..."}` (with a clear explanation)
  for a destructive match, or `{"decision": "allow"}` otherwise.
- Normal commands (e.g. `ls`, `git status`, `npm test`) are never blocked.
- `DELETE FROM ... WHERE ...` is allowed — only a `DELETE` with no `WHERE` is
  blocked.

## Test

```bash
./test.sh
```
