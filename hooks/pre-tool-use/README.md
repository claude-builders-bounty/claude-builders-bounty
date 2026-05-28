# Pre-tool-use Hook: Block Destructive Commands

A Claude Code hook that intercepts dangerous bash commands before they are executed.

## Installation (2 commands)

```bash
# Install Python version (recommended)
cp -r hooks/pre-tool-use ~/.claude/hooks/

# OR install Bash version
chmod +x hooks/pre-tool-use/block_destructive.sh
cp -r hooks/pre-tool-use ~/.claude/hooks/
```

## Hooks Configuration

Add to your `~/.claude/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "name": "block-destructive",
        "hook": "~/.claude/hooks/pre-tool-use/block_destructive.py"
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` | Recursive forced removal |
| `DROP TABLE` | Database drop table |
| `git push --force` | Force push to remote |
| `TRUNCATE` | Database truncate |
| `DELETE FROM` without WHERE | Unconditional data deletion |

## Log Location

Blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Format: `[TIMESTAMP] BLOCKED: command | Project: path`

## Exit Codes

- `0`: Command allowed
- `1`: Command blocked
