# Claude Code Pre-tool-use Security Hook

A robust Python `pre-tool-use` hook that intelligently intercepts and blocks dangerous commands before Claude Code can execute them.

## Features
- **Blocks Destructive Patterns**: Prevents `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.
- **Audit Logging**: Logs every single blocked attempt to `~/.claude/hooks/blocked.log` with the exact timestamp, the attempted command, and the project's current working directory.
- **Safe Interaction**: Does not interfere with normal bash commands or standard tool usage.

## Setup Instructions (2 Commands)

Run these two commands in your terminal to instantly install the hook:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it! Claude Code will now automatically execute this hook before any tool runs to block dangerous operations.
