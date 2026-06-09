# Claude Code Pre-Tool-Use Safety Hook

Blocks dangerous bash commands before Claude executes them.

## Install

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use.py
```

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /tmp/*` |
| `DROP TABLE` | `DROP TABLE users;` |
| `DELETE FROM` (no WHERE) | `DELETE FROM orders;` |
| `git push --force` | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `sudo rm -rf` | `sudo rm -rf /etc/nginx` |
| Block device writes | `dd if=x of=/dev/sda` |
| Fork bombs | `:(){ :|:& };:` |
| Mass permission changes | `chmod -R 777 /` |

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-06-09T12:00:00Z","command":"rm -rf /","project":"/home/user/project","reason":"rm -rf"}
```
