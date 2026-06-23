# Pre-Tool-Use Hook: Block Destructive Bash Commands

A Claude Code pre-tool-use hook that prevents accidental data loss.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

- `rm -rf`, `rm -fr`, `rm -rf /`
- `DROP TABLE`, `TRUNCATE`
- `DELETE FROM` (without WHERE awareness)
- `git push --force`, `git push -f`
- Pipe-to-shell: `curl | bash`, `wget -O - | sh`
- Destructive disk commands: `dd if=`, `> /dev/sda`
- Fork bombs: `:(){ :|:& };:`
- Mass permission changes: `chmod -R 777 /`

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`.
