# destructive-guard — PreToolUse hook for Claude Code

Blocks dangerous bash commands before the agent runs them: `rm -rf`,
`DROP TABLE`, `TRUNCATE`, `DELETE FROM` without `WHERE`, `git push --force`,
`git reset --hard origin/...`, `mkfs`, `dd of=/dev/...`, fork bombs.

Every block is logged to `~/.claude/hooks/blocked.log` as
`timestamp<TAB>project-path<TAB>rule<TAB>command`, and Claude sees a clear
explanation of why the command was denied.

## Install (2 commands)

```bash
cp hooks/destructive-guard.py ~/.claude/hooks/
# then merge hooks/settings.snippet.json into ~/.claude/settings.json
# (the "hooks" key — see snippet for exact shape)
```

## How it works

Claude Code pipes the tool-call event JSON to the hook on stdin before each
`Bash` call. Exit `0` = allow; exit `2` = deny with stderr shown to Claude.
Non-Bash tools and unreadable events pass through — the hook never interferes
with normal commands.

## Test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/tmp"}' \
  | python hooks/destructive-guard.py; echo "exit=$?"   # → blocked, exit=2

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp"}' \
  | python hooks/destructive-guard.py; echo "exit=$?"   # → allowed, exit=0
```
