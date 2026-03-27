# Pre-Tool-Use Hook: Destructive Command Blocker

A Claude Code hook that intercepts dangerous bash commands before they execute. Catches `rm -rf`, `DROP TABLE`, force pushes, and more — then blocks them with a clear explanation.

## What It Blocks

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -fr` | Irreversible recursive deletion |
| `DROP TABLE` | Permanent database table removal |
| `git push --force` / `git push -f` | Overwrites remote git history |
| `TRUNCATE TABLE` | Deletes all table rows |
| `DELETE FROM` (no `WHERE`) | Deletes all rows from a table |

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks/pre-tool-use && \
curl -sL https://raw.githubusercontent.com/DrGalio/claude-builders-bounty/main/hooks/pre-tool-use/pre-tool-use.sh -o ~/.claude/hooks/pre-tool-use/pre-tool-use.sh && chmod +x ~/.claude/hooks/pre-tool-use/pre-tool-use.sh
```

> Requires `jq` (`sudo apt install jq` or `brew install jq`)

## How It Works

1. Claude Code sends the tool call as JSON to the hook via stdin
2. The hook inspects the `command` field for dangerous patterns
3. If blocked → logs to `~/.claude/hooks/blocked.log` and returns exit code 2
4. If safe → exits 0 and lets the command through

## Blocked Log

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:

```
[2026-03-27T04:30:00Z] BLOCKED | Command: rm -rf /data | Reason: Recursive force delete (rm -rf) — risk of irreversible data loss | Path: /home/user/project
```

## Testing

```bash
chmod +x test-hook.sh && ./test-hook.sh
```

## Uninstall

```bash
rm -rf ~/.claude/hooks/pre-tool-use
```

*(Yes, this is one command the hook would block if you tried it through Claude Code. Run it in your terminal directly.)*
