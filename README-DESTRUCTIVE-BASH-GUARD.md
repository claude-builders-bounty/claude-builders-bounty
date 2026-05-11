# Destructive Bash Guard for Claude Code

PreToolUse hook that blocks destructive Bash commands before Claude Code runs them.

## Install in 2 commands

```bash
chmod +x install-destructive-bash-guard.sh hooks/destructive_bash_guard.py
./install-destructive-bash-guard.sh
```

The installer copies the hook to `~/.claude/hooks/destructive_bash_guard.py` and registers it in `~/.claude/settings.json` under `hooks.PreToolUse` for the `Bash` tool.

## What it blocks

- `rm -rf` variants, including `rm -fr` and separated `rm -r -f`
- `git push --force`, `git push -f`, `git push --force-with-lease`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` without a `WHERE` clause

Safe commands such as `ls -la`, `git push origin main`, test commands, and `DELETE FROM ... WHERE ...` are allowed.

## Claude Code hook behavior

The hook reads the PreToolUse JSON event from stdin and returns Claude Code's `hookSpecificOutput` permission decision format:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: ..."
  }
}
```

Allowed commands return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
```

## Logging

Every blocked attempt is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each record contains:

- `timestamp`
- `command`
- `project_path`
- `reason`

## Verification

```bash
python3 test_destructive_bash_guard.py
```

Expected output:

```text
test_destructive_bash_guard.py: ok
```
