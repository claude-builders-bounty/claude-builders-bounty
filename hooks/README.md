# PreToolUse: destructive bash guard

Blocks irreversible bash/SQL/git commands **before** Claude Code executes them.

| Rule | Blocks |
|------|--------|
| `rm_rf` | `rm -rf`, `rm -fr` |
| `drop_table` | `DROP TABLE` |
| `truncate` | `TRUNCATE` |
| `delete_from_no_where` | `DELETE FROM` without `WHERE` |
| `git_push_force` | `git push --force` / `-f` / `--force-with-lease` |

Safe commands (`npm test`, `git push origin branch`, `rm file.txt`, `DELETE FROM t WHERE id=1`) pass through untouched.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre_tool_use_block_destructive.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre_tool_use_block_destructive.py
```

```bash
printf '%s\n' '{' '  "hooks": {' '    "PreToolUse": [' '      {' '        "matcher": "Bash",' '        "hooks": [' '          {' '            "type": "command",' '            "command": "python3 ~/.claude/hooks/pre_tool_use_block_destructive.py"' '          }' '        ]' '      }' '    ]' '  }' '}' > ~/.claude/settings.json
```

> Merge the `hooks` key into an existing `~/.claude/settings.json` if you already have one.

## Behavior

- **Allow** → exit `0`
- **Block** → exit `2` + reason on stderr (Claude can self-correct)
- **Log** → append-only `~/.claude/hooks/blocked.log`  
  Format: `ISO-8601-UTC <TAB> rule_id <TAB> cwd <TAB> command <TAB> reason`

## Tests

```bash
python3 hooks/test_pre_tool_use_block_destructive.py -v
```
