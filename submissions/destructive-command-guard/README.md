# Destructive Command Guard

A Claude Code **pre-tool-use hook** that blocks dangerous bash commands before they execute. Protects against accidental data loss from `rm -rf /`, `DROP TABLE`, force-pushes to main, and more.

## Install (2 commands)

```bash
# 1. Copy the hook script
mkdir -p ~/.claude/hooks && curl -fsSL https://raw.githubusercontent.com/mattfo0/claude-builders-bounty/destructive-command-guard/submissions/destructive-command-guard/guard.sh -o ~/.claude/hooks/guard.sh && chmod +x ~/.claude/hooks/guard.sh

# 2. Add the hook to your Claude Code settings (~/.claude/settings.json)
cat <<'SETTINGS'
Add this to your ~/.claude/settings.json (create the file if it doesn't exist):

{
  "hooks": {
    "pre-tool-use": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ~/.claude/hooks/guard.sh"
          }
        ]
      }
    ]
  }
}
SETTINGS
```

Or manually: copy `guard.sh` to `~/.claude/hooks/guard.sh` and merge `settings-snippet.json` into `~/.claude/settings.json`.

## What Gets Blocked

| Pattern | Blocked | Allowed |
|---------|---------|--------|
| `rm -rf` | `rm -rf /`, `rm -rf ~`, `rm -rf .` | `rm -rf node_modules/`, `rm -rf ./dist` |
| `DROP TABLE` | All `DROP TABLE` statements | -- |
| `TRUNCATE` | All `TRUNCATE` statements | -- |
| `DELETE FROM` | Without a `WHERE` clause | `DELETE FROM users WHERE id = 1` |
| `git push --force` | To `main`/`master` or bare (no branch) | `git push --force origin feature-branch` |

All pattern matching is **case-insensitive** and handles extra whitespace.

Normal commands (`ls`, `git status`, `npm install`, `cat`, etc.) pass through without interference.

## How It Works

1. Claude Code invokes the hook before every `Bash` tool call, passing JSON on stdin
2. The hook extracts the command string and checks it against dangerous patterns
3. If a pattern matches: exits with code **2** (block), prints a message for Claude, and logs to `~/.claude/hooks/blocked.log`
4. If no pattern matches: exits with code **0** (allow) -- zero overhead for safe commands

### Log Format

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```
2026-03-27T15:30:00Z | BLOCKED | rm -rf targeting root... | project=/home/user/myapp | command=rm -rf /
```

## Customize

**Add your own patterns** by adding a new check block in `guard.sh`. The pattern is simple:

```bash
if printf '%s' "$NORMALIZED" | grep -iqE '\bYOUR_PATTERN\b'; then
    block "Reason this is dangerous"
fi
```

**Change the log location** by setting `CLAUDE_HOOKS_DIR`:

```bash
export CLAUDE_HOOKS_DIR=/path/to/logs
```

## Testing

Run the included test suite:

```bash
bash test.sh
```

This validates all blocked and allowed patterns with 35 test cases.

## Files

| File | Purpose |
|------|--------|
| `guard.sh` | The hook script (pre-tool-use) |
| `settings-snippet.json` | Claude Code settings to wire up the hook |
| `test.sh` | Test suite (35 cases) |
| `README.md` | This file |

## License

MIT
