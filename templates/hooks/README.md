# 🛡️ Claude Code Security Hook

Blocks dangerous bash commands before Claude Code executes them.

## Install

```bash
# 1. Copy the hook
mkdir -p ~/.claude/hooks && cp pre-tool-use.py ~/.claude/hooks/pre-tool-use

# 2. Make executable
chmod +x ~/.claude/hooks/pre-tool-use
```

Done. Claude Code will now block dangerous commands automatically.

## What Gets Blocked

| Pattern | Risk |
|---------|------|
| `rm -rf` / `rm -fr` | Recursive forced deletion — irreversible |
| `DROP TABLE` / `DROP DATABASE` / `DROP SCHEMA` | Database destruction |
| `TRUNCATE` | Bulk data deletion |
| `DELETE FROM` (no WHERE) | Unfiltered row deletion |
| `git push --force` / `git push -f` | History rewriting |

## Logs

Blocked commands are logged to `~/.claude/hooks/blocked.log`:

```
[2026-05-28 01:45:00] BLOCKED | project=/home/user/myapp | reason=Recursive forced deletion | cmd=rm -rf /data
```

## Temporary Disable

```bash
mv ~/.claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use.disabled
# Re-enable:
mv ~/.claude/hooks/pre-tool-use.disabled ~/.claude/hooks/pre-tool-use
```

## How It Works

Claude Code calls `pre-tool-use` hooks before executing every tool.
This hook intercepts only `Bash` tool calls, analyzes the command against
a list of dangerous patterns, and blocks execution with a clear explanation.
Safe commands pass through without any latency.

## Resources

- [Claude Code Hooks Documentation](https://docs.anthropic.com/claude-code/hooks)
