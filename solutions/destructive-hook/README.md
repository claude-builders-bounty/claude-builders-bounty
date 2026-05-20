# Destructive Command Blocker Hook

A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.

## Installation

1. Create the hooks directory:
   ```bash
   mkdir -p ~/.claude/hooks
   ```

2. Copy the hook script:
   ```bash
   cp pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh
   chmod +x ~/.claude/hooks/pre-tool-use.sh
   ```

Or one-liner:
```bash
mkdir -p ~/.claude/hooks && curl -o ~/.claude/hooks/pre-tool-use.sh https://raw.githubusercontent.com/YOUR_REPO/main/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## What It Blocks

The hook blocks these dangerous patterns:

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | System destruction |
| `rm -rf /*` | System destruction |
| `rm -rf ~` | Home directory destruction |
| `DROP TABLE` | SQL data loss |
| `DROP DATABASE` | SQL data loss |
| `TRUNCATE TABLE` | SQL data loss |
| `DELETE FROM` without WHERE | Accidental data deletion |
| `git push --force` | History destruction |
| `git push -f` | History destruction |
| `git reset --hard HEAD~` | Uncommitted work loss |
| `:(){ :\|:& };:` | Fork bomb |
| `> /dev/sda` | Disk destruction |
| `mkfs` | Filesystem destruction |

## How It Works

1. Intercepts bash commands before execution via Claude Code's pre-tool-use hook
2. Analyzes command against dangerous pattern database
3. Blocks execution if a dangerous pattern is detected
4. Logs blocked attempts to `~/.claude/hooks/blocked.log`
5. Returns a clear message to Claude explaining why the command was blocked

## Log Format

Blocked attempts are logged with:
```
[2026-05-20T10:30:45Z] BLOCKED: rm -rf /home/user/project
  Pattern: rm -rf with dangerous path
  Project: /home/user/project
  Reason: Potentially destructive command blocked
```

## Configuration

You can customize blocked patterns by editing the `BLOCKED_PATTERNS` array in the script.

## Testing

Test the hook safely:
```bash
# Should be blocked
echo '{"tool":"bash","command":"rm -rf /"}' | ~/.claude/hooks/pre-tool-use.sh

# Should pass
echo '{"tool":"bash","command":"ls -la"}' | ~/.claude/hooks/pre-tool-use.sh
```

## License

MIT