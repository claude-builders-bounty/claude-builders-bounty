# Block Destructive — Claude Code PreToolUse Hook

Blocks dangerous shell commands before they execute, with clear explanations.

## Installation (2 steps)

```bash
cp block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh
```

## Usage

Add to your `~/.claude/settings.json` or `claude/settings.json`:

```json
{
  "hooks": {
    "matcher": "Bash",
    "hooks": [
      {
        "type": "command",
        "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/block-destructive.sh"
      }
    ]
  }
}
```

## What It Blocks

| Command | Why |
|---------|-----|
| `rm -rf` | Permanent file deletion |
| `git push --force` | Rewrites remote history |
| `DROP TABLE` | Destructive DDL |
| `TRUNCATE` | Mass row deletion |
| `DELETE FROM` (without `WHERE`) | Unfiltered row deletion |

## What It Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project directory.

## What It Allows

Everything else — normal file operations, safe git commands, SELECT queries, git push (without --force), etc. — passes through without interference.
