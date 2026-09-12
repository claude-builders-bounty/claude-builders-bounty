# pre-tool-use hook (Issue #3)

A Claude Code hook that blocks dangerous shell commands before they execute and logs every block to
`~/.claude/hooks/blocked.log`.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

## Install (2 commands)

```bash
mkdir -p "$HOME/.claude/hooks"
cp hook/pre-tool-use "$HOME/.claude/hooks/pre-tool-use"
chmod +x "$HOME/.claude/hooks/pre-tool-use"
```

Then configure your Claude Code hook command to invoke:
`$HOME/.claude/hooks/pre-tool-use` with command input as `$1`.

## Behavior

- Safe commands pass through unchanged.
- Blocked commands print a reason and return non-zero.
- Every blocked command is appended with timestamp, reason, project path, and full command to
  `~/.claude/hooks/blocked.log`.
