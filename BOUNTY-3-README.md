# Bounty #3 — Destructive Bash Command Blocker

Claude Code `PreToolUse` hook that denies dangerous Bash commands before they run.

## Install (1 command)

```bash
./install.sh
```

## What it blocks

| Pattern | Example |
|---------|---------|
| `rm -rf` | `rm -rf /tmp/build`, `rm --recursive --force dist/` |
| `DROP TABLE` | `DROP TABLE users;` |
| `git push --force` | `git push --force origin main`, `git push -f` |
| `TRUNCATE` | `TRUNCATE TABLE logs;` |
| `DELETE FROM` without `WHERE` | `DELETE FROM sessions;` |

`git push --force-with-lease` is allowed (safer force-push variant).

Blocked attempts append JSON lines to `~/.claude/hooks/blocked.log`:

```json
{"timestamp":"2026-07-03T12:00:00Z","command":"rm -rf ./dist","project_path":"/home/dev/myproject"}
```

## Verify

```bash
./tests/test-block-destructive.sh
```

Manual smoke test:

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf ./demo"},"cwd":"/tmp/project"}' \
  | ~/.claude/hooks/block-destructive.sh
```

Safe commands produce no stdout and exit 0.

## Claude Code settings snippet

Registered automatically by `install.sh`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```
