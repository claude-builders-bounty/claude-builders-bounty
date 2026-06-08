# Claude Code destructive command blocker

A dependency-free Claude Code `PreToolUse` hook that stops dangerous Bash commands before they run.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/pre-tool-use-blocker && bash scripts/install.sh
```

Then paste the hook block printed by the installer into your Claude Code settings.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with timestamp, attempted command, and project path.

## Verify

```bash
bash scripts/type-check.sh
bash scripts/test.sh
bash scripts/lint.sh
bash scripts/build.sh
```
