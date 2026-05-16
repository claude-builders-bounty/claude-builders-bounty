# Destructive Bash Guard

A [Claude Code](https://docs.anthropic.com/claude-code) hook that intercepts and blocks dangerous bash commands before they execute.

## Installation

```bash
python3 install.py
```

That's it. Restart Claude Code and the hook is active.

## What It Blocks

| Pattern | Example | Risk |
|---------|---------|------|
| Recursive force delete | `rm -rf /etc` | Permanent data loss |
| Root deletion | `rm /` | System destruction |
| Destructive git push | `git push --force` | History overwrite |
| Database destruction | `DROP TABLE`, `DROP DATABASE` | Data loss |
| Table wipe | `TRUNCATE`, `DELETE FROM` without `WHERE` | Unintended data loss |
| Wide-open permissions | `chmod -R 777` | Security vulnerability |
| Remote pipe to shell | `curl URL \| bash` | Remote code execution |
| Block device writes | `dd if=/dev/zero of=/dev/sda` | Filesystem corruption |
| System shutdown | `shutdown`, `reboot` | Service disruption |

## Safe Commands NOT Affected

Normal operations like `ls`, `cd`, `git push` (without `--force`), `npm install`, `docker build`, `pnpm dev`, etc. pass through without interference.

## Logs

All blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-05-16T12:00:00Z", "command": "rm -rf /tmp/data", "matched_patterns": ["rm -rf"], ...}
```

## Uninstall

```bash
python3 uninstall.py
```

## Disable Temporarily

```bash
mv ~/.claude/hooks/block-destructive-bash.py{,.disabled}
```

Re-enable: `mv ~/.claude/hooks/block-destructive-bash.py{.disabled,}`

## Tests

```bash
python3 -m unittest tests/test_block_destructive_bash.py -v
```

## How It Works

The hook implements the Claude Code [PreToolUse](https://docs.anthropic.com/claude-code/hooks) interface. Before every bash command, it:
1. Reads the command from stdin
2. Checks against 16 dangerous patterns
3. If matched: logs the attempt and returns a deny decision with explanation
4. If clean: allows the command through
