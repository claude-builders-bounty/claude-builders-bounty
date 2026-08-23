# Safety Pre-Tool-Use Hook

Blocks destructive bash commands (`rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, and `DELETE FROM` without `WHERE`) before Claude Code executes them. Blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre_tool_use_hook.py https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre_tool_use_hook.py
chmod +x ~/.claude/hooks/pre_tool_use_hook.py
```

*Note: Update your `.claude.json` or global `settings.json` to register this hook for the `PreToolUse` event.*
