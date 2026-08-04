# Destructive Bash Guard Hook

This Claude Code `PreToolUse` hook blocks Bash commands that match common
destructive patterns before they run.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with a timestamp,
the attempted command, the project path, and the block reason.

## Install

From this repository:

```bash
HOOK_DIR="$HOME/.claude/hooks"
mkdir -p "$HOOK_DIR" && \
  cp hooks/destructive-bash-guard/destructive_bash_guard.py \
    "$HOOK_DIR/destructive_bash_guard.py" && \
  chmod +x "$HOOK_DIR/destructive_bash_guard.py"
```

Add this matcher to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/destructive_bash_guard.py"
          }
        ]
      }
    ]
  }
}
```

Claude Code sends Bash tool calls to the script as JSON on stdin. Safe commands
exit silently. Blocked commands return a `PreToolUse` denial with a clear reason
so Claude can choose a narrower, reversible command instead.

## Examples

Allowed:

```bash
ls -la
git status
DELETE FROM sessions WHERE expires_at < now();
```

Blocked:

```bash
rm -rf dist
git push --force origin main
DROP TABLE users;
TRUNCATE audit_events;
DELETE FROM sessions;
```

## Test

```bash
python -m unittest hooks/destructive-bash-guard/test_destructive_bash_guard.py
```
## Navigation

- [Back to `claude-builders-bounty`](../../README.md)
- [Back to `REPOS`](../../../README.md)
- [Back to `AI_REVENUE_SPRINT_100_24H`](../../../../README.md)
