# Destructive Command PreToolUse Hook

This Claude Code `pre-tool-use` hook blocks Bash commands that can destroy files, database contents, or git history.

## Install

```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use.py ~/.claude/hooks/pre-tool-use.py && chmod +x ~/.claude/hooks/pre-tool-use.py
```

```bash
printf '%s\n' '{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"~/.claude/hooks/pre-tool-use.py"}]}]}}' > ~/.claude/settings.json
```

## Blocked Commands

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON with a timestamp, attempted command, project path, and matched pattern.

Normal Bash commands return a `PreToolUse` `permissionDecision` of `allow` and continue without log noise. Blocked commands return `permissionDecision: "deny"` with a clear reason.

## Test

```bash
bash hooks/test-pre-tool-use.sh
```
