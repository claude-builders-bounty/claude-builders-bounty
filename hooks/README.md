# block-dangerous-commands

A Claude Code `pre-tool-use` hook that intercepts destructive bash commands
before they run.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-dangerous-commands.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-dangerous-commands.py
```

Then register the hook in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {"matcher": "Bash",
       "hooks": [{"type": "command",
                  "command": "python3 ~/.claude/hooks/block-dangerous-commands.py"}]}
    ]
  }
}
```

## What it blocks

| Pattern | Example |
|---|---|
| `rm -rf` / `rm -fr` | `rm -rf /data` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` (and `-f`) | `git push --force origin main` |
| `TRUNCATE` | `TRUNCATE TABLE events;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions;` |

`DELETE FROM ... WHERE ...` is allowed. Normal commands are untouched: the
hook exits 0 immediately for any non-matching command or non-Bash tool.

## What happens on a block

- Exit code 2: Claude Code cancels the tool call.
- A stderr message explains to Claude exactly why the command was blocked.
- The attempt is appended to `~/.claude/hooks/blocked.log` as
  `timestamp<TAB>project-path<TAB>command`.

## Test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/x"},"cwd":"/repo"}' \
  | python3 hooks/block-dangerous-commands.py; echo "exit=$?"
# Blocked: recursive/forced delete ... exit=2
```
