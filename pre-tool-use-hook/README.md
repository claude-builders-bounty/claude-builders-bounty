# Claude Code Pre-Tool-Use Security Hook

A `pre-tool-use` hook that intercepts dangerous bash commands before execution,
protecting you from accidental data loss.

## Installation (2 commands)

```bash
# Option 1: Python version (recommended — more robust JSON parsing)
ln -s ~/.claude/hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use

# Option 2: Bash version (no Python dependency)
ln -s ~/.claude/hooks/pre-tool-use-blocker.sh ~/.claude/hooks/pre-tool-use
```

Then **restart Claude Code** — the hook activates on startup.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` or `rm -rf <dir>` | Recursive force delete |
| `dd if=... of=/dev/...` | Direct disk overwrite |
| `mkfs.*` | Filesystem destruction |
| `fdisk -l` | Partition table read (warning) |
| `DROP TABLE <name>` | Database table deletion |
| `TRUNCATE TABLE <name>` | Full table wipe |
| `DELETE FROM <table>` (no WHERE) | Data loss — entire table emptied |
| `git push --force` / `git push -f` | Overwrites shared remote history |
| Fork bomb `:(){ :\|:& };:` | System resource exhaustion |

## How It Works

1. Hook reads JSON from Claude Code's stdin (tool_name, tool_input)
2. Extracts the bash command
3. Matches against dangerous patterns
4. If blocked: logs to `~/.claude/hooks/blocked.log` + exits 1 (command rejected)
5. If clean: exits 0 (command allowed)

## Log File

Every blocked attempt is logged:

```
[2026-04-16 10:30:15] BLOCKED: rm -rf /home/user/project | rm -rf — recursive force delete | Path: /home/user/project
```

## Disable Temporarily

```bash
# Rename the hook file (Claude Code won't find it)
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled

# ... do your dangerous work ...

# Re-enable
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

## Requirements

- **Python version**: Python 3.7+ (recommended)
- **Bash version**: bash 4+, `grep`, `cut` (usually pre-installed on Linux/macOS)
