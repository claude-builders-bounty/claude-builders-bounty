# Block Destructive Commands Hook for Claude Code

A pre-tool-use hook that intercepts dangerous bash commands before Claude Code executes them.

## What It Blocks

| Pattern | Reason |
|---------|--------|
| `rm -rf /`, `rm -rf ~`, `rm -rf *` | Recursive force deletion of system dirs |
| `DROP TABLE` | Irreversible database table removal |
| `TRUNCATE TABLE` / `TRUNCATE <table>` | Removes all rows from a table |
| `DELETE FROM` (without `WHERE`) | Deletes all rows from a table |
| `git push --force` / `git push -f` | Force-pushes overwrite remote history |

Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
- Timestamp (UTC)
- The attempted command
- Project path

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks && cp hooks/block-destructive.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "hooks": {
    "preToolUse": [
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

## How It Works

1. The hook reads the tool invocation JSON from stdin
2. If the tool is `Bash`, it extracts the command string
3. It checks the command against a list of destructive patterns
4. For `DELETE FROM`, it verifies a `WHERE` clause is present
5. If blocked: returns a JSON decision with a clear reason, and logs the attempt
6. If safe: passes the original input through unchanged

## Normal Commands Pass Through

```bash
ls -la                    # passes
git commit -m "fix"       # passes
DELETE FROM users WHERE id = 5  # passes (has WHERE)
rm -rf node_modules       # passes (not root/home/glob)
```

## Example Blocked Log Entry

```
[2026-05-20T14:30:00Z] Blocked command: rm -rf / | Project: /home/user/my-app
[2026-05-20T14:31:22Z] Blocked command: DROP TABLE users | Project: /home/user/my-app
```

## Uninstall

Remove the entry from `~/.claude/settings.json` and delete the file:

```bash
rm ~/.claude/hooks/block-destructive.sh
```