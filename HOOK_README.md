# Destructive Bash Command Hook

`hooks/block-dangerous-bash.sh` is a Claude Code `PreToolUse` hook that blocks
dangerous Bash commands before they run. It blocks `rm -rf`, `git push --force`,
`DROP TABLE`, `TRUNCATE`, and `DELETE FROM` without a `WHERE` clause.

When a command is blocked, the hook writes a line to
`~/.claude/hooks/blocked.log` with the timestamp, attempted command, project
path, and reason. Safe Bash commands and non-Bash tools exit silently so Claude
Code's normal permission flow is unchanged.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-dangerous-bash.sh ~/.claude/hooks/block-dangerous-bash.sh && chmod +x ~/.claude/hooks/block-dangerous-bash.sh
mkdir -p .claude && cp .claude/settings.example.json .claude/settings.local.json
```

## Test

```bash
bash tests/run-hook-tests.sh
```
