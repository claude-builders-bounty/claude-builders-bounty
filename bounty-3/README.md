# Destructive Bash Guard for Claude Code

A dependency-free `PreToolUse` hook that stops destructive Bash commands before Claude Code executes them.

## Acceptance criteria

The guard blocks:

- `rm -rf`, `rm -fr`, split flags such as `rm -r -f`, and long-form recursive/force flags
- `DROP TABLE`
- `git push --force`, `git push -f`, and `--force-with-lease`
- `TRUNCATE`
- `DELETE FROM ...` when that SQL statement has no `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- attempted command
- project path
- blocking reason

Claude receives a structured `PreToolUse` deny decision explaining why the command was blocked.

## Install — one command

From the repository root:

```bash
python bounty-3/install.py
```

The installer copies the hook to `~/.claude/hooks/destructive_bash_guard.py`, marks it executable, and adds the Bash `PreToolUse` entry to `~/.claude/settings.json` without deleting existing settings. Running the installer again is safe and does not duplicate the hook entry.

A static configuration example is also available in `bounty-3/settings.example.json`.

## False-positive resistance

The hook parses shell command structure rather than searching the entire string with one regex. That means harmless commands that merely mention dangerous text continue to work:

```bash
echo "rm -rf /"
grep "DROP TABLE" schema.sql
printf "git push --force origin main"
psql -c "SELECT 'DROP TABLE users';"
```

It also recognizes common real execution wrappers:

```bash
sudo rm -rf /tmp/demo
env FOO=1 rm --recursive --force build/
bash -c 'rm -rf /tmp/demo'
```

## Examples

Blocked:

```bash
rm -r -f build/
sudo rm -rf /tmp/demo
git -C repo push --force-with-lease origin main
psql -c 'DROP TABLE users'
sqlite3 app.db 'TRUNCATE TABLE events'
psql -c 'DELETE FROM users'
```

Allowed:

```bash
rm build/output.txt
git push origin feature/safe-branch
psql -c 'DELETE FROM sessions WHERE expires_at < now()'
echo "rm -rf /"
python -m pytest
```

## Test

```bash
python -m unittest -v tests/test_destructive_bash_guard.py
```

The suite verifies required destructive patterns, split/long flags, sudo/env/shell wrappers, harmless mentions, SQL string literals, per-statement `WHERE` handling, comments, JSONL logging, Claude's deny response, non-Bash passthrough, and idempotent installation.

## Design note

This is a focused safety guard, not a complete shell or SQL parser. Commands outside the bounty's destructive patterns still fall through to Claude Code's normal permission system.
