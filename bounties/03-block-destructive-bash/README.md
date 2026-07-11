# PreToolUse hook: block destructive bash

Claude Code hook that **denies** destructive shell commands before they run.

**Bounty:** #3 — $100 (Opire)

## Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm -fr` | `rm -rf ./dist` |
| `DROP TABLE` | SQL drop |
| `TRUNCATE` | SQL truncate |
| `git push --force` / `-f` | force push |
| `DELETE FROM` without `WHERE` | mass delete |

Safe commands pass through. Every block is appended to `~/.claude/hooks/blocked.log` as:

```text
timestamp<TAB>project_path<TAB>reason<TAB>command
```

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

Then merge this into `~/.claude/settings.json` (or project `.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

One-liner settings merge is left to you so we never overwrite your existing hooks array blindly.

## Test

```bash
python3 test_block_destructive_bash.py
```

## How it works

1. Claude Code invokes the hook with a JSON payload on stdin.
2. The hook extracts `tool_input.command` for Bash tools.
3. On match → write log line, print reason on stderr, exit `2` (block).
4. Otherwise exit `0` (allow).
