# Pre-tool-use Hook: Block Destructive Bash Commands

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before they are executed.

## Features

- Blocks destructive commands: `rm -rf`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without WHERE, `git push --force`, and more
- Logs every blocked attempt to `~/.claude/hooks/blocked.log` with timestamp, command, and project path
- Displays a clear message explaining why the command was blocked
- Does not interfere with normal bash commands

## Installation (2 commands)

```bash
cd issue-3-hook
python3 install.py
```

Or manually:

```bash
cp block-destructive.py ~/.claude/hooks/block-destructive.py
chmod +x ~/.claude/hooks/block-destructive.py
```

Then add to `~/.claude/hooks/settings.json`:

```json
{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "command": "python3 ~/.claude/hooks/block-destructive.py"
      }
    ]
  }
}
```

## Testing

```bash
python3 test_hook.py
```

## Blocked Patterns

| Pattern | Example |
|---------|---------|
| `rm -rf` / `rm --force` | `rm -rf /tmp/test` |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE users;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |
| `git push --force` / `-f` | `git push --force origin main` |
| `chmod 777` | `chmod 777 /etc/passwd` |
| `mkfs` | `mkfs.ext4 /dev/sda1` |
| `dd` to device | `dd if=/dev/zero of=/dev/sda` |
| `sudo rm` | `sudo rm -rf /var/log` |

## Log Format

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```json
{"timestamp": "2026-06-19 13:00:00 UTC", "command": "rm -rf /", "reason": "rm -rf or rm --force detected", "project_path": "/home/user/project"}
```

## How It Works

The hook receives Claude Code's tool-use input via stdin, extracts the bash command, and checks it against blocked patterns using regex. If a match is found, it logs the attempt and exits with code 2 (which tells Claude Code to block the tool use).
