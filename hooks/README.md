# Destructive Bash Guard Hook

Blocks rm -rf, DROP TABLE, TRUNCATE, git push --force, DELETE without WHERE.

### Install (2 commands)
```bash
mkdir -p ~/.claude/hooks && cp hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
echo '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"$HOME/.claude/hooks/block_destructive.py"}]}]}}' > ~/.claude/settings.json
```

Logs all blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, project path.
