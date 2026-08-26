# Destructive Bash Command Block Hook

A Claude Code `PreToolUse` hook for the `Bash` tool. It reads Claude Code's JSON hook input from stdin and blocks destructive commands before execution.

## Install (1 command)

```bash
bash hook/install.sh
```

The installer copies the hook to `~/.claude/hooks/block_hook.py` and safely adds a `Bash` `PreToolUse` entry to `~/.claude/settings.json` without replacing existing settings.

## Blocked operations

- `rm -rf` and equivalent recursive + force flag combinations
- `DROP TABLE`
- `git push --force` / `-f` (including force-with-lease variants)
- `TRUNCATE`
- `DELETE FROM ...` when that SQL statement has no `WHERE` clause

Normal commands exit successfully and are not modified.

## Audit log

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each record contains the timestamp, attempted command, project path, and block reason.

## What Claude sees

A blocked command exits with status `2`, which Claude Code treats as a blocking `PreToolUse` result. The hook also returns the structured `permissionDecision: deny` payload and a clear message explaining the block.

## Test

```bash
python3 hook/test_block_hook.py
```

The tests cover all five required destructive patterns, safe commands, `DELETE ... WHERE`, non-Bash tools, and the required audit-log fields.
