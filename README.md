# Claude Code Safe Bash Hook

This is a `pre-tool-use` hook for Claude Code that prevents the agent from accidentally executing destructive bash or SQL commands. 

It intercepts the input to tools like `Bash` or `run_command` and applies regex rules to block:
- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` (without a `WHERE` clause)

If a command is blocked, the hook rejects the tool call and logs the attempt (with timestamp, project path, and attempted command) to `~/.claude/hooks/blocked.log`.

## Installation (1 Command)

Just create the hooks directory and copy the script into place, making it executable:

```bash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/pre-tool-use.py > ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Requirements
- Python 3+ 
- Claude Code (`@anthropic-ai/claude-code`)

## How it Works
When Claude attempts to run a bash tool, this script is invoked automatically. The script reads the JSON tool payload from `STDIN`. If the payload contains a `command` or `script` key that matches a destructive pattern, the hook exits with status `1` and prints an error message, which Claude sees and aborts the execution. Safe commands exit with status `0` and run normally.
