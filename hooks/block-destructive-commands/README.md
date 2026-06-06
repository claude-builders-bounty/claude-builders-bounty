# Block Destructive Commands — Claude Code PreToolUse Hook

A [Claude Code](https://code.claude.com/docs/en/hooks) `PreToolUse` hook that intercepts dangerous bash commands before they execute.

## What it blocks

| Pattern | Why |
|---------|-----|
| `rm -rf` / `rm --recursive --force` | Recursive force delete |
| `DROP TABLE` | SQL table destruction |
| `git push --force` / `git push -f` | Rewrites remote history |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM ...` (without `WHERE`) | Unconditional SQL row deletion |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use.py
cp settings.json ~/.claude/settings.json
```

Claude Code loads `~/.claude/settings.json` automatically on the next session.

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

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
