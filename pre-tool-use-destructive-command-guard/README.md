# PreToolUse Destructive Command Guard

Claude Code `PreToolUse` hook that blocks destructive Bash commands before they run.

## Install

```bash
chmod +x pre-tool-use-destructive-command-guard/install.sh pre-tool-use-destructive-command-guard/hooks/block-dangerous-bash.py
pre-tool-use-destructive-command-guard/install.sh
```

The installer copies the hook to `~/.claude/hooks/block-dangerous-bash.py` and adds a `PreToolUse` Bash matcher to `~/.claude/settings.json`.

Set `CLAUDE_CONFIG_HOME` to install into a different Claude config directory:

```bash
CLAUDE_CONFIG_HOME=/tmp/claude-test pre-tool-use-destructive-command-guard/install.sh
```

## What It Blocks

- `rm -rf`, `rm -fr`, `rm -r -f`, `rm --recursive --force`
- `git push --force`, `git push -f`, `git push --force-with-lease`
- `DROP TABLE`
- `TRUNCATE`
- `DELETE FROM ...` without a `WHERE` clause in the same SQL statement

Every blocked attempt is appended to `~/.claude/hooks/blocked.log` with a timestamp, attempted command, project path, and matched rule. If `CLAUDE_CONFIG_HOME` is set, the log is written to `$CLAUDE_CONFIG_HOME/hooks/blocked.log`.

## Claude Code Hook Format

The installed settings entry uses the current `PreToolUse` hook format:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /absolute/path/to/.claude/hooks/block-dangerous-bash.py"
          }
        ]
      }
    ]
  }
}
```

When a command is denied, the hook returns:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked potentially destructive Bash command: ..."
  }
}
```

Normal Bash commands exit successfully without output, so the hook does not bypass Claude Code's normal permission flow.

## Test

```bash
python3 -m unittest discover pre-tool-use-destructive-command-guard/tests
```
