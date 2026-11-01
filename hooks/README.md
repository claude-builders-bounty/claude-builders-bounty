# destructive-command hook

A Claude Code `PreToolUse` hook that blocks dangerous bash commands before
they run, logs every blocked attempt, and explains to Claude why it was stopped.

Blocks: `rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force` / `-f`,
and `DELETE FROM` without a `WHERE` clause.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.py
```

Then register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

## What it does

- Intercepts every `Bash` tool call before execution.
- Allows normal commands through unchanged.
- On a match, blocks the command, prints a JSON decision with a clear reason,
  and appends a line to `~/.claude/hooks/blocked.log`:
  `timestamp \t reason \t project-path \t command`.
- Fails open: an internal error never blocks your session.

## Test it

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"},"cwd":"/tmp/demo"}' \
  | python3 ~/.claude/hooks/block-destructive.py
```

Expected output: `{"decision": "block", "reason": "..."}` and a new line in
`~/.claude/hooks/blocked.log`.

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"},"cwd":"/tmp/demo"}' \
  | python3 ~/.claude/hooks/block-destructive.py
```

Expected output: nothing (command allowed).

## License

MIT
