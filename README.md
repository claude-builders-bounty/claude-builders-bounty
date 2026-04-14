# Claude Code Pre-Tool-Use Safety Hook

> ⛔ Block destructive bash commands before they execute — with logging and clear explanations.

## What It Does

This **Claude Code `PreToolUse` hook** intercepts dangerous bash commands (like `rm -rf /`, `DROP TABLE`, `git push --force`) **before** they execute, logs every blocked attempt, and tells Claude exactly why it was blocked.

## Dangerous Patterns Blocked

| Pattern | Risk |
|---------|------|
| `rm -rf` (non-root paths) | Irreversible file deletion |
| `DROP TABLE` / `TRUNCATE` | Database destruction |
| `DELETE FROM` (without WHERE) | Accidental data wipe |
| `git push --force` / `-f` | Rewrite shared history |
| `dd if=/dev/zero`, `mkfs`, `> /dev/sd*` | Disk wiping |
| `chmod -R 777 /` | Security hole |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/pre-tool-use-block-destructive.sh -o ~/.claude/hooks/pre-tool-use-block-destructive.sh && chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.sh
```

Then add to your Claude Code settings:

```bash
echo '{"hooks":{"PreToolUse":[{"type":"command","command":"bash ~/.claude/hooks/pre-tool-use-block-destructive.sh"}]}}' > ~/.claude/settings.local.json
```

## How It Works

1. Claude Code sends tool-use JSON to stdin before each bash execution
2. Hook extracts the command and checks against dangerous regex patterns
3. If matched → **blocks** the command, logs to `~/.claude/hooks/blocked.log`, returns a clear explanation
4. If safe → passes through unchanged, zero overhead

## Log Format

Every blocked attempt is logged with timestamp, command, pattern, and project path:

```
[2026-04-14T14:00:00Z] command="rm -rf ./node_modules" pattern="rm\s+-rf?\s+[^/]" path="/home/user/project"
```

## Customize

Edit the `DANGEROUS_PATTERNS` array in the script to add or remove patterns. Each entry is a PCRE (Perl-compatible) regex.

## License

MIT
