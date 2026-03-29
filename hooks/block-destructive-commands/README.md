# 🛡️ Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) pre-tool-use hook that intercepts dangerous bash commands **before** they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm --recursive --force` | Recursive force delete — irreversible data loss |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Permanent schema destruction |
| `git push --force` / `git push -f` | Rewrites shared remote history |
| `TRUNCATE [TABLE]` | Non-rollbackable row removal |
| `DELETE FROM` without `WHERE` | Deletes every row in the table |

## What it does NOT block

| Command | Why it's safe |
|---------|---------------|
| `rm -r` (no `-f`) | Prompts for confirmation |
| `git push --force-with-lease` | Checks remote ref before force-pushing |
| `DELETE FROM ... WHERE ...` | Targeted deletion with conditions |
| Normal commands (`ls`, `pip install`, etc.) | Not destructive |

## Install (2 commands)

```bash
# 1. Copy hook + config into your project
cp -r hooks/block-destructive-commands/.claude /path/to/your/project/

# 2. Done — Claude Code picks up .claude/settings.json automatically
```

Or from this repo:

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/cbb && \
cp -r /tmp/cbb/hooks/block-destructive-commands/.claude . && rm -rf /tmp/cbb
```

## Requirements

- **Python 3.6+** — no external dependencies (no jq, no pip install needed)

## Testing

```bash
cd hooks/block-destructive-commands
python3 -m pytest tests/test_block_destructive.py -v
```

## Blocked log

Blocked attempts are logged as structured JSON to `~/.claude/hooks/blocked.log`:

```bash
cat ~/.claude/hooks/blocked.log
```

Example entry:

```json
{"timestamp":"2026-03-29T07:00:00+00:00","event":"BLOCKED","command":"rm -rf /important","reason":"Recursive force delete (rm -rf) is blocked — can cause irreversible data loss. Command: rm -rf /important","cwd":"/home/user/project"}
```

## Configuration

The hook lives in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## How to unblock

Run the command directly in your terminal. The hook only intercepts commands **Claude Code** tries to execute — not your own shell.

## License

MIT
