# Claude Code Destructive Command Blocker

Pre-tool-use hook that blocks dangerous bash commands before execution.

## Installation (2 commands)

```bash
# 1. Clone this repository
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git

# 2. Copy hook to Claude Code hooks directory
cp hooks/block-destructive.sh ~/.claude/hooks/
```

## Features

- Blocks: `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without WHERE
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`
- Clear error messages explaining why commands were blocked
- Does not interfere with normal bash commands

## Usage

The hook automatically activates when Claude Code executes bash commands.
Blocked commands are logged with timestamp, command, and project path.

## License

MIT
