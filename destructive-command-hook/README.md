# Destructive Bash command safety hook for Claude Code

A Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they run.

It blocks:

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSON Lines with:

- UTC timestamp
- attempted command
- project path
- matched pattern

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
python3 destructive-command-hook/install_settings.py
```

The installer creates or updates `~/.claude/settings.json` with a `PreToolUse` hook for the Bash tool:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## How it works

Claude Code sends hook payloads like this before running Bash commands:

```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "cwd": "/path/to/project",
  "tool_input": {
    "command": "rm -rf /tmp/build"
  }
}
```

When the command matches a blocked pattern, the hook returns a Claude Code `PreToolUse` denial:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Destructive Bash command blocked by Claude Code safety hook: matched rm -rf..."
  }
}
```

Normal Bash commands exit with no output and continue untouched.

## Manual settings alternative

If you do not want to run the installer, add this to `~/.claude/settings.json` yourself:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```

## Test locally

Allowed command:

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"npm test"}}' | python3 destructive-command-hook/block_destructive_bash.py
```

Blocked command:

```bash
printf '%s\n' '{"hook_event_name":"PreToolUse","tool_name":"Bash","cwd":"/tmp/demo","tool_input":{"command":"rm -rf /tmp/demo"}}' | python3 destructive-command-hook/block_destructive_bash.py
```

Then inspect:

```bash
tail -n 1 ~/.claude/hooks/blocked.log
```
