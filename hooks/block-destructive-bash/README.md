# Block Destructive Bash Commands

Claude Code `PreToolUse` hook that blocks dangerous Bash commands before they execute.

## Install

```bash
chmod +x hooks/block-destructive-bash/install.sh
./hooks/block-destructive-bash/install.sh
```

The installer copies the hook into `~/.claude/hooks/` and adds a `PreToolUse` matcher for the Bash tool in `~/.claude/settings.json`.

## What It Blocks

- `rm -rf` and `rm -fr` style recursive forced deletion
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause
- `git push --force`, `git push --force-with-lease`, and `git push -f`

Normal Bash commands continue through the default Claude Code permission flow.

## Logging

Every blocked attempt is appended to:

```text
~/.claude/hooks/blocked.log
```

Each JSONL entry includes:

- UTC timestamp
- Attempted command
- Project path
- Block reason

## Manual Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/demo"},"cwd":"/tmp/project"}' | ~/.claude/hooks/block_destructive_bash.py
```

Expected output:

```json
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Blocked destructive Bash command: rm -rf style recursive forced deletion."}}
```

Safe commands produce no output and exit successfully.
