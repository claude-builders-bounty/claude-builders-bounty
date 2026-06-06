# Pre-Tool-Use Bash Safety Hook

This bounty submission adds a Claude Code `PreToolUse` hook that blocks a short list of destructive Bash commands before they run.

## What it blocks

- `rm -rf`
- `git push --force`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## What it does when it blocks

- Returns a Claude Code `PreToolUse` denial with a clear reason
- Writes the blocked command to `~/.claude/hooks/blocked.log`
- Records the current working directory and UTC timestamp

## Install

Run one command from the repo root:

```bash
python pre-tool-use-hook/install_hook.py
```

That command copies the hook into `~/.claude/hooks/` and updates `~/.claude/settings.json` so Bash calls are checked automatically.

## Verify

After install, a command like this should be blocked:

```bash
rm -rf ./build
```

Safe commands still proceed normally, for example:

```bash
echo "hello"
```

## Test

```bash
python -m unittest discover -s pre-tool-use-hook/tests
```
