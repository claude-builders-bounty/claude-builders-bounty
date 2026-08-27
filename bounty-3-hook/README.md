# Claude Code PreToolUse Hook - Block Destructive Commands

This hook intercepts and blocks dangerous Bash commands before Claude Code executes them.

## Features
- Blocks `rm -rf`
- Blocks `DROP TABLE`
- Blocks `git push --force`
- Blocks `TRUNCATE`
- Blocks `DELETE FROM` when there is no `WHERE` clause
- Logs all blocked commands to `~/.claude/hooks/blocked.log`

## Installation

Install in just 2 commands (make sure you have `jq` installed):

```bash
mkdir -p ~/.claude/hooks && cp block_destructive.py ~/.claude/hooks/block_destructive.py && chmod +x ~/.claude/hooks/block_destructive.py

# If ~/.claude/settings.json doesn't exist, create it with the hook, otherwise append to it
if [ ! -f ~/.claude/settings.json ]; then echo '{"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/block_destructive.py"}]}]}}' > ~/.claude/settings.json; else jq '.hooks.PreToolUse += [{"matcher": "Bash", "hooks": [{"type": "command", "command": "~/.claude/hooks/block_destructive.py"}]}]' ~/.claude/settings.json > tmp.json && mv tmp.json ~/.claude/settings.json; fi
```
