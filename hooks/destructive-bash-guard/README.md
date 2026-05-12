# 🛡️ Destructive Bash Guard — Claude Code PreToolUse Hook

A Claude Code `PreToolUse` hook that intercepts dangerous bash commands before execution.

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `rm -rf` | Recursive force delete — irreversible filesystem destruction |
| `rm --no-preserve-root` | Dangerous root-level deletion |
| `DROP TABLE / DROP DATABASE` | Irreversible database object removal |
| `TRUNCATE` | Wipes all rows from a table |
| `DELETE FROM` (without `WHERE`) | Deletes every row in a table |
| `git push --force / -f` | Overwrites remote history |

## Installation (2 commands)

```bash
git clone https://github.com/oceanzhang1204/claude-builders-bounty.git
bash claude-builders-bounty/hooks/destructive-bash-guard/install.sh
```

That's it. The install script:
1. Deploys `pre_tool_use.py` to `~/.claude/hooks/`
2. Registers the hook in `~/.claude/settings.json` (merges with existing config)

## How It Works

The hook follows the [Claude Code hooks protocol](https://docs.anthropic.com/claude-code/hooks):

1. **Receives** a JSON payload on stdin with the tool name and command
2. **Checks** the command against blocked patterns (only for `Bash` tool calls)
3. **If dangerous**: outputs `{"hookSpecificOutput": {"permissionDecision": "deny", ...}}` and exits with code `2` → **blocks execution**
4. **If safe**: exits with code `0` → **allows execution** (zero overhead)

## Logging

Every blocked attempt is appended to `~/.claude/hooks/blocked.log`:

```
[2026-05-12T10:02:30Z] project='/my-project' | reason='rm with -f flag (destructive delete)' | command='rm -rf /tmp/old'
[2026-05-12T10:02:31Z] project='/my-project' | reason='DELETE FROM without WHERE (deletes all rows)' | command='sqlite3 db.sqlite "DELETE FROM logs"'
```

## Testing

```bash
python3 -m unittest test_hook -v
```

25 test cases covering all blocked patterns, safe command pass-through, logging, and the full stdin→stdout pipeline.

## Uninstall

Remove the hook entry from `~/.claude/settings.json` under `hooks.PreToolUse`, then delete `~/.claude/hooks/pre_tool_use.py`.
