# Destructive Command Hook

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they
run, writes an audit record, and returns a structured denial message to Claude.

## Install

```bash
python destructive-command-hook/install.py
python destructive-command-hook/tests/test_block_destructive.py
```

The installer copies the hook into `~/.claude/hooks/`, marks it executable, and
adds this hook entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block_destructive.py"
          }
        ]
      }
    ]
  }
}
```

## What It Blocks

- `rm -rf` and common flag variants such as `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`, including `--force-with-lease`
- `DELETE FROM ...` when the statement has no `WHERE` clause

Normal Bash commands exit successfully without stdout, so Claude Code continues
without extra context or prompts.

## Log File

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each JSONL record includes:

- UTC timestamp
- attempted command
- project path
- matched rule

## Manual Smoke Test

```bash
printf '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"}}' \
  | ~/.claude/hooks/block_destructive.py
```

Expected result:

<!-- markdownlint-disable MD013 -->
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: matched rm -rf. Remove the destructive operation or ask the user for an explicit safer plan."
  }
}
```
<!-- markdownlint-enable MD013 -->
