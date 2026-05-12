# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that denies dangerous Bash commands before they run and records each blocked attempt.

## Install

```bash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/
```

```json
{"hooks":{"PreToolUse":[{"matcher":"Bash","hooks":[{"type":"command","command":"python3 ~/.claude/hooks/block_destructive_commands.py"}]}]}}
```

Put the JSON in `~/.claude/settings.json`, or merge the `hooks` object into your existing settings file.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include `WHERE`

Every blocked command is appended to `~/.claude/hooks/blocked.log` with an ISO timestamp, the attempted command, and the project path reported by Claude Code.

## Manual Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | python3 block_destructive_commands.py
```

Expected response:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: rm -rf"
  }
}
```

Normal commands such as `npm test` return no output and exit successfully.
