# Claude Code Destructive Command Guard

A `PreToolUse` hook for [Claude Code](https://docs.anthropic.com/en/docs/claude-code/hooks) that intercepts and blocks dangerous bash commands before execution.

## Blocked Patterns

| Pattern | Example | Why |
|---|---|---|
| `rm -rf` | `rm -rf /`, `rm -fr .` | Recursive force delete |
| `DROP TABLE` | `DROP TABLE users;` | Destroys database tables |
| `git push --force` | `git push -f origin main` | Overwrites remote history |
| `TRUNCATE` | `TRUNCATE TABLE orders;` | Deletes all rows from table |
| `DELETE FROM` (no `WHERE`) | `DELETE FROM users;` | Deletes all rows |

Safe commands pass through normally — `rm file.txt`, `git push`, `DELETE FROM users WHERE id = 1`, etc.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty && bash install.sh
```

That's it. The installer copies the hook to `~/.claude/hooks/` and registers it in `~/.claude/settings.json`.

## How It Works

```
Claude Code ──► Bash tool call ──► Hook receives JSON on stdin
                                        │
                                   Safe? ──► yes ──► exit 0 (allow)
                                        │
                                        └─► no  ──► log + print reason + exit 2 (block)
```

1. Claude Code invokes the hook before every Bash tool call
2. The hook checks the command against destructive patterns
3. **Safe** → exits 0, command runs normally
4. **Dangerous** → logs the attempt, prints a denial message to Claude, exits 2 to block

## Log Format

Every blocked command is appended to `~/.claude/hooks/blocked.log`:

```
[2026-03-27T10:30:00Z] BLOCKED | project: /home/user/myapp | reason: rm -rf (recursive force delete) | command: rm -rf /tmp/data
```

## Configuration

The hook is registered in `~/.claude/settings.json` under `hooks.PreToolUse`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

To temporarily disable, remove the entry from `settings.json`.

## Run Tests

```bash
python3 tests/test_hook.py
```

## Uninstall

```bash
rm ~/.claude/hooks/block-destructive.py
```

Then remove the `PreToolUse` hook entry from `~/.claude/settings.json`.

## Requirements

- Python 3.6+
- Claude Code
