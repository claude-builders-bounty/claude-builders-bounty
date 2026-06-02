# Destructive Command Guard

Claude Code `PreToolUse` hook for the `Bash` tool. It blocks destructive shell commands before they execute, logs the blocked attempt, and returns a clear denial reason to Claude.

## Install

From this repository:

```bash
python3 hooks/destructive-command-guard/tests/test_destructive_command_guard.py
bash hooks/destructive-command-guard/install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive-command-guard.py`, makes it executable, and registers it in `~/.claude/settings.json` for `PreToolUse` events matching `Bash`.

## What It Blocks

- `rm -rf` and equivalent combined-flag forms such as `rm -fr`
- `git push --force`, including `--force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM ...` statements that do not include a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` with an ISO timestamp, project path, and attempted command.

## Hook Response

For blocked commands, the hook emits Claude Code decision JSON:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: ..."
  }
}
```

Safe Bash commands exit with code `0` and no output, so normal usage is not interrupted.
