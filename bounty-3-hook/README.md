# Bounty 3 — Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code PreToolUse hook that intercepts and blocks dangerous commands before they execute.

## Setup (2 commands)

```bash
# 1. Copy the hook to your project or a shared location
cp guard-hook.sh ~/.claude/hooks/guard-hook.sh && chmod +x ~/.claude/hooks/guard-hook.sh

# 2. Add to your Claude Code settings (~/.claude/settings.json)
cat <<'EOF' >> ~/.claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/guard-hook.sh"
          }
        ]
      }
    ]
  }
}
EOF
```

## What it blocks

| Pattern | Example | Why |
|---------|---------|-----|
| `rm -rf` | `rm -rf /`, `rm -rf .` | Recursive force delete can wipe entire filesystems |
| `DROP TABLE` / `DROP DATABASE` | `DROP TABLE users;` | Permanently destroys database objects |
| `git push --force` / `git push -f` | `git push --force origin main` | Rewrites remote history, can lose teammates' work |
| `TRUNCATE TABLE` | `TRUNCATE TABLE sessions;` | Removes all rows without transaction logging |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` | Deletes every row in the table |

## What it allows

| Command | Why |
|---------|-----|
| `rm file.txt` | Single file deletion is fine |
| `rm -r dir/` | Recursive without `-f` prompts for confirmation |
| `git push origin main` | Normal push is safe |
| `git push --force-with-lease` | Safe force push — fails if remote has new commits |
| `DELETE FROM users WHERE id = 5` | Targeted deletion with WHERE clause |
| All other commands | Only the patterns above are blocked |

## How it works

1. Claude Code calls the hook with tool input as JSON on stdin
2. The hook extracts the command string from the JSON payload
3. The command is normalized (lowercased, whitespace collapsed)
4. Each pattern is checked using grep with Perl-compatible regex
5. If a pattern matches: logs to `~/.claude/hooks/blocked.log`, prints reason to stderr, exits with code 2
6. If no pattern matches: exits with code 0 (allow)

## Log format

Blocked attempts are logged as JSON lines to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-04-01T14:30:00Z","reason":"rm-rf","command":"rm -rf /tmp/data","project":"my-app"}
{"timestamp":"2026-04-01T14:31:00Z","reason":"drop-table","command":"DROP TABLE users;","project":"my-app"}
```

## Testing

```bash
bash test-hook.sh
```

Runs 30+ test cases covering all blocked patterns and safe commands. Uses `assert_blocked` / `assert_allowed` helpers with colored pass/fail output.

## Customization

To add new patterns, add a new section in `guard-hook.sh` between the pattern checks:

```bash
# N. Your new pattern
if echo "$NORMALIZED" | grep -qP 'your-regex-here'; then
    block "pattern-name" "Explanation of why this is blocked."
fi
```

To whitelist a specific command, add a check before the pattern matching section that exits 0 early.
