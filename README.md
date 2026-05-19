# Dangerous Command Blocker

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) pre-tool-use hook that intercepts and blocks dangerous bash commands.

**Blocks:** `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, `DELETE FROM` without a `WHERE` clause

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use
curl -sL https://raw.githubusercontent.com/niufox/claude-builders-bounty/main/pre-tool-use.py \
  -o ~/.claude/hooks/pre-tool-use/dangerous-command-blocker.py && chmod +x "$_"
```

## How It Works

- Runs before every tool call in Claude Code
- Only intercepts Bash/terminal commands
- Blocks dangerous patterns and logs details to `~/.claude/hooks/blocked.log`
- Safe commands pass through without interference
- Blocked commands are logged with: timestamp, attempted command, project path

## Log File

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-19 14:30:00] Blocked: rm -rf (recursive force delete)
  Command: rm -rf /important/data
  Project: /Users/me/my-project
  ---
```

## Requirements

- Python 3.6+
- Claude Code CLI

## License

MIT
