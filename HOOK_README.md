# Destructive Command Blocker Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous bash commands before execution.

## Installation

```bash
mkdir -p ~/.claude/hooks
cp block-destructive.sh ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What It Blocks

| Pattern | Risk | Action |
|---------|------|--------|
| `DROP TABLE`, `DROP DATABASE`, `TRUNCATE` | 🔴 High | Blocked |
| `git push --force`, `git reset --hard` | 🔴 High | Blocked |
| `mkfs.*`, `chmod -R 0 /` | 🔴 High | Blocked |
| `wget ... \| bash`, `curl ... \| bash` | 🔴 High | Blocked |
| Fork bombs (`:(){ :\|:& };:`) | 🔴 High | Blocked |
| `sudo rm -rf`, `eval $()` | 🔴 High | Blocked |
| `git push --force-with-lease` | 🟡 Medium | Warning |
| `ALTER TABLE`, `UPDATE ... SET` | 🟡 Medium | Warning |
| `DELETE FROM` | 🟡 Medium | Warning |

## Features

- **Dry-run mode**: `bash block-destructive.sh --dry-run "DROP TABLE users"` — warns without blocking
- **Full logging**: All events logged to `~/.claude/hooks/blocked.log` with timestamps and working directory
- **Smart pattern matching**: Case-insensitive, handles whitespace variations
- **Zero dependencies**: Pure bash, works on any system with bash 4+
- **Exit codes**: 0 = allowed, 1 = blocked

## Testing

```bash
# These should be BLOCKED
bash block-destructive.sh --dry-run "DROP TABLE users"
bash block-destructive.sh --dry-run "git push --force origin main"
bash block-destructive.sh --dry-run "TRUNCATE payments"

# These should be ALLOWED
bash block-destructive.sh "ls -la"
bash block-destructive.sh "git status"
bash block-destructive.sh "echo hello"
```

## Log Output

```
[BLOCKED] 2026-03-15 14:30:00 | cwd: /home/user/project | reason: matched pattern 'DROP\s+TABLE' | cmd: DROP TABLE users
[WARN] 2026-03-15 14:31:00 | cwd: /home/user/project | reason: matched warning pattern 'DELETE FROM' | cmd: DELETE FROM logs
```
