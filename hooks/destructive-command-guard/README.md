# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

It uses Claude Code's structured `hookSpecificOutput.permissionDecision: "deny"`
format for blocked commands. Safe commands exit normally without emitting a
permission decision, so the hook does not bypass Claude Code's normal permission
flow.

## What it blocks

- `rm -rf` / `rm -fr`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, the attempted command, the project path, and the matched rule.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/destructive-command-guard/pre_tool_use.py ~/.claude/hooks/pre_tool_use.py && chmod +x ~/.claude/hooks/pre_tool_use.py
```

```bash
python3 hooks/destructive-command-guard/install.py
```

The installer adds the hook to `~/.claude/settings.json` while preserving existing settings.

Reference: https://code.claude.com/docs/en/hooks

## Test

```bash
python3 -m unittest discover -s hooks/destructive-command-guard/tests
```
