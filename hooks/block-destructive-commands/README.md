# Destructive Commands Block Hook

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they are executed.

## Features
- Blocks highly destructive commands: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- Seamless integration: Doesn't interfere with normal, safe bash commands.
- Audit Logging: Logs every blocked attempt to `~/.claude/hooks/blocked.log` with the timestamp, attempted command, and project path.
- Clear Feedback: Displays an explanatory error message to Claude so the agent understands why the execution failed.

## Installation (2 commands)

Run the following commands in your terminal:

```bash
mkdir -p ~/.claude/hooks
curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block-destructive-commands/pre_tool_use.py -o ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

*Note: Ensure Claude Code is configured to use your local hooks as per the [Anthropic Hooks Documentation](https://docs.anthropic.com/claude-code/hooks).*
