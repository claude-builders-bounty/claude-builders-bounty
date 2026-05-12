# Claude Code Guardian Hook

A `PreToolUse` hook for [Claude Code](https://code.claude.com) that blocks destructive bash commands before they execute.

## What It Blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /important/dir` |
| `git push --force` | `git push --force origin main` |
| `DROP TABLE/DATABASE` | `DROP TABLE users;` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM users;` |

**Important:** `DELETE FROM table WHERE ...` is still allowed — only WHERE-less DELETEs are blocked.

## Install (2 commands)

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git /tmp/cbb
bash /tmp/cbb/submissions/guardian-hook/install.sh
```

Or if already cloned:

```bash
bash install.sh
```

## How It Works

1. Claude Code fires this hook before ANY `Bash` tool use
2. The hook inspects the command via `$CLAUDE_TOOL_INPUT`
3. Dangerous patterns → exit code 2 (Claude blocks the tool)
4. Safe commands → exit code 0 (tool proceeds normally)

## Verification

```bash
# Test that the hook blocks dangerous commands
echo '{"command": "rm -rf /tmp/test"}' | python3 ~/.claude/hooks/pre-tool-use-guardian.py
echo "Exit code: $?"  # Should be 2 (blocked)

# Test that safe commands pass
echo '{"command": "ls -la"}' | python3 ~/.claude/hooks/pre-tool-use-guardian.py
echo "Exit code: $?"  # Should be 0 (allowed)
```

## Logs

Blocked attempts are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-12T23:15:00Z] BLOCKED [DESTRUCTIVE DELETE]
  Project: /home/user/my-project
  Command: rm -rf /tmp/*
  Reason:  rm -rf or equivalent recursive-force removal detected
```

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use-guardian.py
# Manually remove the PreToolUse hook from ~/.claude/settings.json
```

## Files

```
├── README.md
├── install.sh
└── hooks/
    └── pre-tool-use-guardian.py
```
