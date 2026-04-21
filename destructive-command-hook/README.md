# Destructive Command Blocker Hook

A Claude Code `PreToolUse` hook that blocks dangerous `Bash` commands before they run.

## Install

```bash
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
claude-builders-bounty/destructive-command-hook/install.sh
```

The installer copies `block_destructive_commands.py` to `~/.claude/hooks/` and adds a `PreToolUse` matcher for `Bash` to `~/.claude/settings.json`.

## Blocked Patterns

- `rm -rf`, including combined flags such as `rm -fr`
- `DROP TABLE`
- `git push --force`
- `TRUNCATE`
- `DELETE FROM` without a `WHERE` clause

Blocked attempts are appended to `~/.claude/hooks/blocked.log` as JSON lines with:

- `timestamp`
- `command`
- `project_path`
- `reason`

## Manual Configuration

If you prefer to configure Claude Code manually, copy the script to `~/.claude/hooks/block_destructive_commands.py`, make it executable, and add:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/block_destructive_commands.py"
          }
        ]
      }
    ]
  }
}
```

## Local Test

```bash
printf '{"tool_input":{"command":"rm -rf ./build"},"cwd":"/tmp/demo"}' | python3 block_destructive_commands.py
echo $?
```

The hook exits with code `2`, prints a clear reason to `stderr`, and logs the attempt. Safe commands exit with code `0` and produce no output.
