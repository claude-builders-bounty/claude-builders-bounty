# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that denies dangerous Bash commands before they run and records each blocked attempt.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
```

```bash
sh claude-builders-bounty/hooks/block-destructive-commands/install.sh
```

The installer copies the hook into `~/.claude/hooks/` and registers the Bash `PreToolUse` hook in `~/.claude/settings.json`.

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

## Tests

```bash
python3 -m unittest hooks/block-destructive-commands/test_block_destructive_commands.py
```

The tests cover all required blocked patterns, representative allowed commands, deny JSON output, and blocked-attempt logging.
