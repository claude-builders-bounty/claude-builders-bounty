# Destructive Command Guard — Claude Code Hook

A `pre-tool-use` hook that intercepts dangerous bash commands before Claude Code
executes them.

## Blocked Patterns

| Pattern | Description |
|---------|-------------|
| `rm -rf` | Recursive force delete |
| `DROP TABLE` | Destructive SQL statement |
| `TRUNCATE` | Destructive SQL statement |
| `git push --force` / `-f` | Force push to remote |
| `DELETE FROM` (no WHERE) | Unscoped SQL delete |

## Installation

```bash
git clone https://github.com/anthropics/claude-builders-bounty.git && bash claude-builders-bounty/hooks/install.sh
```

Or if you already have the repo cloned:

```bash
bash hooks/install.sh
```

That's it — the hook is active immediately for all Claude Code sessions.

## How It Works

1. Claude Code calls the hook before executing any `Bash` tool invocation
2. The hook checks the command against the blocked patterns
3. If matched, it **blocks** the command, logs the attempt, and tells Claude why
4. If not matched, the command proceeds normally

## Log File

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- UTC timestamp
- Attempted command
- Reason for blocking
- Project working directory

## Uninstall

Remove the hook entry from `~/.claude/settings.json` and delete the script:

```bash
rm ~/.claude/hooks/block_destructive.py
```

## Testing

Run the test suite:

```bash
python3 -m pytest hooks/test_block_destructive.py -v
```
