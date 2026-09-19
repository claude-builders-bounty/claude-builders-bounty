# Hook: block destructive bash commands ($100 bounty #3)

Claude Code `PreToolUse` hook. Inspects every `Bash` command before it runs,
blocks the destructive ones, lets everything else through.

## Install (2 commands)

```sh
mkdir -p ~/.claude/hooks && cp hooks/block-destructive-bash.py ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive-bash.py
```

Then register in `~/.claude/settings.json`:

```json
{ "hooks": { "PreToolUse": [{ "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/hooks/block-destructive-bash.py" }] }] } }
```

## What it blocks

- `rm -rf` aimed at `/`, `~`, `$HOME`, `*`, `.`, `..` (narrow targets like `rm -rf ./build` pass)
- `DROP TABLE`, `TRUNCATE`
- `git push --force` / `git push -f`
- `DELETE FROM <table>` without a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as
`timestamp | cwd=<project path> | command=<attempted command>`,
and Claude sees a message explaining why it was blocked.

## Test

```sh
HOOK_BLOCKED_LOG=/tmp/blocked.log sh -c 'for c in "ls -la" "rm -rf /" "git push --force"; do echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$c\"},\"cwd\":\"/tmp\"}" | python3 hooks/block-destructive-bash.py; echo "$c -> exit $?"; done'
```

Expected: `ls -la -> exit 0`, `rm -rf / -> exit 2`, `git push --force -> exit 2`.
