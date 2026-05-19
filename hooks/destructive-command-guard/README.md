# Destructive Command Guard

Claude Code `PreToolUse` hook for Bash commands. It blocks destructive shell or SQL
operations before they run and records each block in `~/.claude/hooks/blocked.log`.

## Install

```bash
python3 hooks/destructive-command-guard/install.py
```

Restart Claude Code after installation so the updated `~/.claude/settings.json`
is loaded.

## What It Blocks

- `rm -rf` and equivalent recursive + force flag combinations, because a typo can
  remove more than the intended directory.
- `DROP TABLE`, because schema deletion should be an explicit database migration,
  not an incidental shell command.
- `git push --force`, `git push -f`, and `git push --force-with-lease`, because
  rewriting remote history can erase collaborators' work.
- `TRUNCATE`, because it removes table or file contents without row-level review.
- `DELETE FROM` statements without a `WHERE` clause, because they delete every row.

Safe commands such as `ls`, `git push origin main`, `rm file.txt`, and
`DELETE FROM sessions WHERE id = ?` are allowed.

## Hook Configuration

The installer copies the hook to `~/.claude/hooks/pre-tool-use-block-destructive.py`
and adds this Claude Code settings entry:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/pre-tool-use-block-destructive.py"
          }
        ]
      }
    ]
  }
}
```

Claude Code passes hook input as JSON on stdin. When the command is blocked, the
hook returns a `PreToolUse` `permissionDecision: deny` response with a clear reason
for Claude and writes a JSON line containing timestamp, attempted command,
blocked pattern, reason, and project path to `blocked.log`.
