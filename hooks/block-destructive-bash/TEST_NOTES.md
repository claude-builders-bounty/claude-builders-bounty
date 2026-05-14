# Test Notes

## Documentation Basis

Claude Code hooks documentation says `PreToolUse` hooks receive JSON on stdin,
including `tool_name`, `tool_input.command`, and `cwd` for Bash calls. A
blocking command hook can stop execution by returning exit code `2`; stderr is
shown back to Claude as the reason.

Reference: https://code.claude.com/docs/en/hooks

## Commands Run

```bash
python -m py_compile hooks/block-destructive-bash/block_destructive_bash.py hooks/block-destructive-bash/test_block_destructive_bash.py
python hooks/block-destructive-bash/test_block_destructive_bash.py
```

Result:

```text
Ran 5 tests in 0.001s
OK
```

Installer test was run with a temporary `HOME` and `USERPROFILE` so it did not
modify the real `~/.claude` directory. It created:

```text
~/.claude/settings.json
~/.claude/hooks/block_destructive_bash.py
~/.claude/hooks/blocked.log
```

## Hook Simulation Results

The hook was tested with Claude-style `PreToolUse` JSON input:

| Command | Expected | Result |
|---|---:|---:|
| `rm -rf dist` | 2 | 2 |
| `rm -Rf dist` | 2 | 2 |
| `sqlite3 app.db "DROP TABLE users"` | 2 | 2 |
| `psql -c "TRUNCATE audit_log"` | 2 | 2 |
| `sqlite3 app.db "DELETE FROM users"` | 2 | 2 |
| `sqlite3 app.db "DELETE FROM users WHERE id = 1"` | 0 | 0 |
| `git push --force origin main` | 2 | 2 |
| `git -C repo push --force origin main` | 2 | 2 |
| `git push --force-with-lease origin main` | 2 | 2 |
| `git push origin main` | 0 | 0 |
| `npm test` | 0 | 0 |
| `truncate -s 0 file.log` | 0 | 0 |

Blocked attempts wrote JSON Lines records to `blocked.log` with:

- timestamp
- attempted command
- project path
- reason
