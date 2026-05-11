# Claude Code Destructive Command Hook

A `PreToolUse` hook that blocks dangerous Bash commands before execution.

**Blocks:** `rm -rf`, `git push --force`, `DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`

**Logs:** All blocked attempts to `~/.claude/hooks/blocked.log` with timestamp, command, and project path.

## Installation

```bash
# Install in 2 commands:
mkdir -p .claude/hooks && cp settings.json .claude/settings.json && cp hooks/pre-tool-use .claude/hooks/
chmod +x .claude/hooks/pre-tool-use
```

## How it works

- The hook runs before every Bash command in Claude Code
- If the command contains destructive patterns, it's **denied** with an explanation
- Non-destructive commands pass through without interference
- All blocks are logged for review

## Files

| File | Purpose |
|------|---------|
| `.claude/settings.json` | Hook configuration (project scope) |
| `.claude/hooks/pre-tool-use` | Python script that inspects commands |
