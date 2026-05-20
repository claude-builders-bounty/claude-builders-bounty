# Destructive Bash Guard Hook

Claude Code `PreToolUse` command hook that blocks high-risk Bash commands before they run.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
bash claude-builders-bounty/hooks/destructive-bash-guard/install.sh
```

The installer copies the hook to `~/.claude/hooks/destructive-bash-guard.py`, makes it executable, and adds a `PreToolUse` Bash matcher to `~/.claude/settings.json`. If an existing settings file is present, a `.bak` copy is written before the update.

## What It Blocks

- `rm -rf` and flag variants such as `rm -fr`
- `git push --force`, `git push -f`, `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Safe commands exit with no output so Claude Code continues normally. Blocked commands return:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command ..."
  }
}
```

Blocked attempts are appended as JSON lines to `~/.claude/hooks/blocked.log` with timestamp, project path, rule, reason, and command.

## Manual Configuration

If you do not want the installer to update settings, copy `pre_tool_use.py` to a stable path and add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/absolute/path/to/pre_tool_use.py"
          }
        ]
      }
    ]
  }
}
```

## Test

```bash
python3 -m unittest hooks/destructive-bash-guard/tests/test_pre_tool_use.py
```
