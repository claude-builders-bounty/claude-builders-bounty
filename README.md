# Block Destructive Bash — Claude Code pre-tool-use hook

Blocks dangerous shell commands before Claude Code runs them. Logs every block to `~/.claude/hooks/blocked.log`.

## Blocks
- `rm -rf` / `rm -fr` (and `-r…f` flag combos)
- `DROP TABLE`
- `TRUNCATE` / `TRUNCATE TABLE`
- `DELETE FROM …` without a `WHERE` clause
- `git push --force` / `git push -f`

Normal bash commands are left alone.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block_destructive.py
```

```bash
mkdir -p ~/.claude && printf '%s\n' '{' '  "hooks": {' '    "PreToolUse": [' '      {' '        "matcher": "Bash",' '        "hooks": [' '          {' '            "type": "command",' '            "command": "python3 ~/.claude/hooks/block_destructive.py"' '          }' '        ]' '      }' '    ]' '  }' '}' > ~/.claude/settings.json
```

(If you already have `~/.claude/settings.json`, merge the `PreToolUse` Bash hook that runs `python3 ~/.claude/hooks/block_destructive.py` instead of overwriting.)

Bash alternative: use `.claude/hooks/block-destructive.sh` the same way (`command`: `bash ~/.claude/hooks/block-destructive.sh`).

## Log format
Each blocked attempt appends one line:

`ISO8601_UTC | project=<path> | command=<attempted command>`

## Why Claude sees a clear message
On block, the hook exits non-zero and prints the reason on stderr so Claude Code refuses the tool call and shows the explanation.
