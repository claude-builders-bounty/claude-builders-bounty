# SKILL: Block Destructive Bash Commands

## What It Does

A `pre-tool-use` hook for Claude Code that intercepts and blocks dangerous bash commands before they execute. It protects users from accidental data loss by rejecting high-risk operations with a clear explanation.

## Installation

```bash
mkdir -p ~/.claude/hooks
curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/block-destructive-hook/hook.sh -o ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Or 2 commands (as required by acceptance criteria):

```bash
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/skills/block-destructive-hook/hook.sh -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## How It Works

### Hook Architecture

The hook follows Claude Code's `pre-tool-use` hook format:

1. Claude Code invokes `~/.claude/hooks/pre-tool-use bash` before any bash tool execution
2. The hook receives the bash command via stdin
3. It checks against a set of destructive patterns
4. If a match is found: logs to `~/.claude/hooks/blocked.log` and exits with code 70 (block)
5. If no match: exits with code 0 (allow)

### Blocked Patterns

| Pattern | Risk | Example |
|---------|------|---------|
| `rm -rf /, ~, /*` | Recursive force delete | `rm -rf /` or `rm -rf ~` |
| `DROP TABLE` | Irreversible schema deletion | `DROP TABLE users;` |
| `TRUNCATE TABLE` | Removes all rows instantly | `TRUNCATE TABLE logs;` |
| `git push --force` | Overwrites remote history | `git push --force origin main` |
| `git push -f` | Force push short form | `git push -f` |
| `DELETE FROM` without WHERE | Deletes entire table | `DELETE FROM users;` |
| `mkfs` | Formats entire disk | `sudo mkfs.ext4 /dev/sda1` |
| `dd of=/dev/sd*` | Direct block device write | `dd if=/dev/zero of=/dev/sda` |
| `shred -zuz` | Secure file deletion | `shred -zuz sensitive.pdf` |
| `DROP DATABASE` | Deletes entire database | `DROP DATABASE production;` |
| `truncate --size=0` | Empties files | `truncate -s 0 access.log` |

### Override

Users can bypass the block for a specific command using the `--confirm` flag:

```
--confirm  # Claude Code per-command approval
```

## Logging

All blocked commands are logged to `~/.claude/hooks/blocked.log` with:

```
[TIMESTAMP] TOOL=bash PROJECT=/path/to/project REASON=description COMMAND=the command
```

Example log entry:
```
[2026-04-02 10:30:15] TOOL=bash PROJECT=/home/user/project REASON=DROP TABLE detected — this permanently deletes a database table COMMAND=DROP TABLE users;
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Allow command (no dangerous patterns detected) |
| 70 | Block command (dangerous pattern detected) |

## Files

- `hook.sh` — The main hook script
- `README.md` — This file
