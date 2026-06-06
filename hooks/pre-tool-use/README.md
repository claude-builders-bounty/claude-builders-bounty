# 🔒 Bash Safety Hook — pre-tool-use

Blocks destructive bash commands inside Claude Code. Zero configuration.

## Blocks These Commands

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -r` / `rm -f` | Destructive recursive delete |
| `DROP TABLE` / `DROP DATABASE` | Data loss in SQL |
| `git push --force` / `git push -f` | Rewrites remote history |
| `TRUNCATE` | Destructive SQL |
| `DELETE FROM` **without** `WHERE` | Unconditional row deletion |

## Installation

**One command:**

```bash
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

Or manually:
```bash
mkdir -p ~/.claude/hooks
# Copy pre-tool-use into ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Claude Code picks up hooks automatically on next start.

## How It Works

1. Claude Code calls the hook before every tool execution
2. The hook checks the command against dangerous patterns
3. Safe commands pass through normally
4. Dangerous commands are blocked with a clear message and logged to `~/.claude/hooks/blocked.log`

## Logs

Blocked commands are timestamped and logged to:
```
~/.claude/hooks/blocked.log
```

Format: `[timestamp] project=/path | reason=why | cmd=blocked command`

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```
