# block-destructive — Claude Code security hook

Pre-tool-use hook that intercepts dangerous bash commands before execution.

## Install

```bash
cp block-destructive.py ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/block-destructive.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## Patterns Blocked

| Pattern | Examples |
|---------|----------|
| `rm -rf` | `rm -rf /`, `rm -fr node_modules`, `rm --recursive --force *` |
| `git push --force` | `git push -f origin main`, `git push --force-with-lease` |
| `DROP TABLE/DATABASE` | `DROP TABLE users;`, `DROP DATABASE prod;` |
| `TRUNCATE` | `TRUNCATE users;`, `TRUNCATE TABLE logs;` |
| `DELETE` without WHERE | `DELETE FROM users;` (heuristic) |
| `dd` / `mkfs` | `dd if=/dev/zero of=/dev/sda`, `mkfs.ext4 /dev/sda1` |
| `chmod 777` on system paths | `chmod -R 777 /etc` |
| fork bombs | `:(){ :|:& };:` |
| `curl \| bash` | `curl url \| bash`, `curl url \| sh` |

## Safe Commands Still Work

`npm`, `pip`, `yarn`, `cargo`, `gh`, `echo`, and standard `git` commands
(status/log/diff/add/commit/checkout/branch/stash/pull/fetch/merge/rebase)
are explicitly allowlisted and never blocked.

## Log

Blocked attempts are written to `~/.claude/hooks/blocked.log` as JSON lines:

```json
{"timestamp":"2026-06-15T14:00:00+00:00","attempted_command":"rm -rf /tmp/*","project_path":"/home/user/project"}
```

## Verify

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/test"},"cwd":"/tmp"}' \
  | python ~/.claude/hooks/block-destructive.py
echo "Exit code: $?"  # should be 2

echo '{"tool_name":"Bash","tool_input":{"command":"npm run build"},"cwd":"/tmp"}' \
  | python ~/.claude/hooks/block-destructive.py
echo "Exit code: $?"  # should be 0
```

## Uninstall

Remove the hook entry from `~/.claude/settings.json` and delete the script.
