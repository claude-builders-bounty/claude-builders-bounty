# Pre-Tool-Use Safety Hook for Claude Code

Blocks destructive bash commands before they execute.

## What It Blocks

| Category | Examples |
|----------|----------|
| Filesystem | `rm -rf /`, `mkfs`, `dd if=/dev/`, `format C:` |
| Git | `git push --force`, `git reset --hard HEAD~`, `git clean -fd` |
| Database | `DROP TABLE`, `DELETE FROM`/`UPDATE` without `WHERE` |
| System | `chmod -R 0`, `chown -R`, `sudo rm` |
| Docker | `docker system prune -a`, `docker rmi -f` |
| Eval | `eval $(curl...)`, `exec $(...)` |

## Warning Mode (allowed, with notice)

- Pushes to remote (`git push`, `npm publish`, `twine upload`)
- External script execution (`curl | sh`, `wget | bash`)
- Config file edits (`package.json`, `.env`, `Dockerfile`)
- Remote transfers (`scp`, `rsync` to servers)

## Installation

```bash
bash hooks/pre-tool-use/install.sh
```

Or manually:

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use/pre_tool_use.py ~/.claude/hooks/
claude config set hooks.pre_tool_use ~/.claude/hooks/pre_tool_use.py
```

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log` with timestamps.
