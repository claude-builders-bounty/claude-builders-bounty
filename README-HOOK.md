# Bash Safety Hook

Pre-tool-use hook that blocks destructive bash commands in Claude Code.

## Install (2 commands)

```bash
# 1. Clone and copy hook files
git clone https://github.com/<YOUR_USERNAME>/claude-builders-bounty.git && cd claude-builders-bounty && cp -r .claude hooks .

# 2. Make hook executable
chmod +x .claude/hooks/pre-bash-hook.sh
```

## What it blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /` | Permanent directory deletion |
| `DROP TABLE` | Database destruction |
| `git push --force` | History rewrite |
| `TRUNCATE TABLE` | Bulk data removal |
| `DELETE FROM` without WHERE | Accidental full-table delete |

## How it works

- Listens on `PreToolUse` event for `Bash` tool
- Reads JSON stdin, extracts `.tool_input.command`
- Matches against deny patterns using `grep -Eiq`
- Exit `0` = allow, Exit `2` = block (message sent to Claude)
- Logs all blocked attempts to `~/.claude/hooks/blocked.log`

## Log format

```
[2026-06-15T08:30:00Z] BLOCKED: 'rm -rf /tmp/data' [cwd: /home/user/project]
```
