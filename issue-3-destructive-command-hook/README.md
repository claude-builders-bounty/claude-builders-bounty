# Destructive Command Guard

Claude Code `PreToolUse` hook for issue #3. It blocks destructive Bash commands before execution and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## Install

From the repository root:

```bash
python3 issue-3-destructive-command-hook/install.py
```

The installer copies `block_destructive_commands.py` to `~/.claude/hooks/` and adds a `PreToolUse` entry for the `Bash` tool in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf`, including combined flags like `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Allowed commands exit silently with no hook decision, so normal Bash commands continue through the usual Claude Code permission flow.

## Blocked Log

Each blocked attempt appends one JSON line to:

```text
~/.claude/hooks/blocked.log
```

Each log entry includes `timestamp`, `attempted_command`, `project_path`, and `reason`.

## Test

```bash
python3 -m unittest issue-3-destructive-command-hook/test_block_destructive_commands.py
```

## Hook Output

When a command is blocked, the hook returns a Claude Code decision in this shape:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: <reason>. The command was not executed."
  }
}
```
