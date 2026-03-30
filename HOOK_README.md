# Claude Code Pre-tool-use Hook

A safety hook that blocks destructive bash commands before they are executed by Claude Code.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use-hook.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Blocked Commands

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Irreversible file deletion |
| `DROP TABLE/DATABASE` | Database destruction |
| `TRUNCATE` | Table data wipe |
| `DELETE FROM` (without WHERE) | Full table delete |
| `git push --force` | History rewrite |
| `mkfs` | Disk formatting |
| `dd if=/dev/zero` | Disk wipe |
| `chmod -R 777` | Dangerous permissions |
| Fork bomb | System crash |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
2026-03-30T23:15:00+08:00|BLOCKED|rm -rf /tmp/test|/home/user/project
```

## Testing

```bash
# Test blocked command
echo '{"tool":{"use":{"bash":{"command":"rm -rf /tmp"}}}}' | ~/.claude/hooks/pre-tool-use

# Test safe command
echo '{"tool":{"use":{"bash":{"command":"ls -la"}}}}' | ~/.claude/hooks/pre-tool-use
```

## License

MIT
