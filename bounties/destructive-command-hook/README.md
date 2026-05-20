# Destructive Command Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

## Install

For a project without existing Claude Code hook settings:

```bash
mkdir -p .claude/hooks && cp bounties/destructive-command-hook/block_destructive_commands.py .claude/hooks/
chmod +x .claude/hooks/block_destructive_commands.py && cp bounties/destructive-command-hook/settings.example.json .claude/settings.json
```

If `.claude/settings.json` already exists, merge the `PreToolUse` entry from `settings.example.json` instead of overwriting your current settings.

## What It Blocks

- `rm -rf`, including common variants such as `rm -fr`, `rm -r -f`, and `sudo rm -rf`
- `git push --force`, `git push -f`, and related force-push flags
- SQL containing `DROP TABLE`
- SQL containing `TRUNCATE`
- SQL containing `DELETE FROM` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- `timestamp`
- `attempted_command`
- `project_path`
- `reason`

## Example

Claude Code sends the hook JSON on stdin:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "cwd": "/work/project",
  "tool_input": {
    "command": "rm -rf dist"
  }
}
```

The hook denies the command with a structured `PreToolUse` decision:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: recursive forced removal with rm. Review the command and ask the user before trying a safer alternative."
  }
}
```

Normal commands exit successfully with no output, so they do not interfere with regular Bash usage.

## Test

```bash
python3 bounties/destructive-command-hook/test_block_destructive_commands.py
```
