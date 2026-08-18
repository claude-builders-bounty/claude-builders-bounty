# Claude Code Security Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they are executed. 

It explicitly blocks:
- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` (without a `WHERE` clause)

When a command is blocked, Claude receives a clear explanation, and the attempt is logged to `~/.claude/hooks/blocked.log` with a timestamp and the current project path.

## Installation

You can install this hook in just 2 commands:

**1. Download the script and make it executable:**
```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use.py https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

**2. Register the hook in your global config (`~/.claude/settings.json`):**
```bash
jq '.hooks.PreToolUse += [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use.py"}]}]' ~/.claude/settings.json > tmp.json && mv tmp.json ~/.claude/settings.json
```
*(If `~/.claude/settings.json` does not exist or is empty, create it with `{ "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ { "type": "command", "command": "python3 ~/.claude/hooks/pre-tool-use.py" } ] } ] } }`)*
