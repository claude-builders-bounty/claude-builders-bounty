# Destructive Bash Command Blocker

This Claude Code `PreToolUse` hook blocks Bash commands that match destructive
patterns before the Bash tool can execute them.

## Installation

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
python3 claude-builders-bounty/hooks/install_destructive_bash_hook.py
```

The installer copies `block_destructive_bash.py` to `~/.claude/hooks/` and
registers it in `~/.claude/settings.json` for the `Bash` tool.

## Blocked Patterns

- `rm` commands that combine recursive and force flags, including `rm -rf`,
  `rm -fr`, `rm -r -f`, and `rm --recursive --force`
- `git push --force`, `git push --force-with-lease`, and `git push -f`
- SQL statements containing `DROP TABLE`
- SQL statements containing `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` as JSONL with:

- UTC timestamp
- attempted command
- project path
- blocking reason

Allowed commands produce no output and do not interfere with normal Bash use.
Blocked commands return a Claude Code hook response with
`permissionDecision: "deny"` and a clear explanation.

## Manual Configuration

If you prefer not to run the installer, copy the hook file yourself and add this
entry to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_bash.py"
          }
        ]
      }
    ]
  }
}
```
