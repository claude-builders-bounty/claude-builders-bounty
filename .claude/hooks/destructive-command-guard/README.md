# Destructive Command Guard

Claude Code `PreToolUse` hook that blocks high-risk Bash commands before they run.

## Install

Run these two commands from the repository root:

```bash
mkdir -p ~/.claude/hooks && cp -R .claude/hooks/destructive-command-guard ~/.claude/hooks/
python3 ~/.claude/hooks/destructive-command-guard/install.py
```

## What It Blocks

- `rm` with both recursive and force flags, such as `rm -rf dist`
- `git push --force`, `git push -f`, and forced refspec pushes such as `git push origin +main`
- SQL `DROP TABLE`
- SQL `TRUNCATE`
- SQL `DELETE FROM` statements that do not include a `WHERE` clause

Normal Bash commands exit with code `0` and produce no output, so Claude Code continues without extra noise.

## Log File

Every blocked command is appended to:

```text
~/.claude/hooks/blocked.log
```

Each entry is JSON Lines and includes:

- `timestamp`
- `project_path`
- `command`
- `rule_id`
- `reason`

## Claude Code Hook Behavior

When a command is blocked, the hook returns Claude Code's structured denial format:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked SQL DELETE FROM without a WHERE clause..."
  }
}
```

## Test

```bash
python3 -m unittest discover .claude/hooks/destructive-command-guard/tests
```

