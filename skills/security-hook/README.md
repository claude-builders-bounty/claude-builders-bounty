# Security Hook — Pre-tool-use

Blocks destructive bash commands before they execute. Works with Claude Code hooks.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

That's it. Restart Claude Code and the hook is active.

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Recursive root deletion |
| `git push --force` | Destructive history rewrite |
| `DROP TABLE/ DATABASE` | Permanent schema destruction |
| `TRUNCATE <table>` | Irreversible row deletion |
| `DELETE FROM <table>` (without WHERE) | Mass data loss |
| `mkfs.*` | Filesystem formatting |
| `dd if=/dev/urandom of=` | Destructive overwrite |
| `chmod 777 /` | Security risk |

## What it allows

Everything else — normal `rm file.txt`, `git push`, `DELETE FROM users WHERE id=1`, etc.

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-17T04:00:00Z] BLOCKED | reason=Recursive force-delete of root (/) | cwd=/home/user/project | cmd=rm -rf /
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```
