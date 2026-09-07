# beamo-command-guard

Claude Code **PreToolUse** hook that blocks destructive bash / SQL commands and logs every attempt.

Relates to [#3](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/3) · Beamo LLC · beamo@beamosupport.com

## Install (2 commands)

```bash
cd beamo-command-guard && bash install.sh
```

That’s it — the installer copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`.

> Requires Python 3. Restart Claude Code (or wait for settings reload) after install.

## What it blocks

| Pattern | Example |
| --- | --- |
| `rm -rf` (recursive + force, any flag order) | `rm -rf /tmp/build`, `rm -fr .`, `rm -r -f dir` |
| `git push --force` / `-f` | `git push --force origin main` |
| `DROP TABLE` | `mysql -e 'DROP TABLE users'` |
| `TRUNCATE` | `psql -c 'TRUNCATE accounts'` |
| `DELETE FROM` **without** `WHERE` | `DELETE FROM users;` |

Safe commands (`ls`, `git status`, `rm file.txt`, `DELETE FROM t WHERE id=1`, …) pass through unchanged.

## Logging

Every block is appended to `~/.claude/hooks/blocked.log`:

```text
2026-09-07T03:15:00Z	/path/to/project	rm -rf /tmp/x	Blocked: `rm` with both recursive...
```

Fields: **timestamp** (UTC), **project path**, **attempted command**, **reason**.

## Manual wiring (optional)

If you prefer not to use `install.sh`, copy `hooks/block-destructive.py` to `~/.claude/hooks/` and merge `hooks/settings.snippet.json` into `~/.claude/settings.json`.

## Tests

```bash
python3 tests/test_hook.py
```

## License

MIT (same as parent repository)
