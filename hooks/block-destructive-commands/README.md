# Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm -fr` / `rm -r -f` / `rm --recursive --force` | Recursive force delete (any flag order) |
| `DROP TABLE` | SQL table destruction |
| `git push --force` / `git push -f` | Rewrites remote history (allows `--force-with-lease`) |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty
bash claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

The installer copies the hook to `~/.claude/hooks/` and merges the `PreToolUse` entry into `~/.claude/settings.json` without overwriting your other hooks.

Uses the official Claude Code `hookSpecificOutput` schema (`permissionDecision: deny`) — not the legacy `decision: block` format.

## How it works

1. Intercepts every `Bash` tool call via the `PreToolUse` hook
2. Checks the command against destructive patterns
3. **Blocks** matching commands and returns a clear denial message to Claude
4. **Logs** every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
5. **Allows** safe commands to pass through unchanged

## Blocked log

```bash
cat ~/.claude/hooks/blocked.log
```

Example entry:

```
[2026-06-06T12:34:56Z] Command: rm -rf /tmp/build | Project: /home/user/project
```

## Tests

From the repository root:

```bash
python3 -m unittest discover -s hooks/block-destructive-commands/tests -v
```

## License

MIT
