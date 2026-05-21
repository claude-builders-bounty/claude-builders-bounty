# Block destructive Bash commands in Claude Code

This is a Claude Code `PreToolUse` hook for issue #3. It blocks destructive Bash commands before execution and writes every blocked attempt to `~/.claude/hooks/blocked.log`.

## What it blocks

- `rm -rf` and `rm -fr`
- `DROP TABLE`
- `TRUNCATE`
- `git push --force`
- `DELETE FROM` without a `WHERE` clause

Normal Bash commands are allowed without output.

## Install in 2 commands

```bash
mkdir -p ~/.claude/hooks && cp issue-3-block-destructive-bash/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
```

```bash
python3 ~/.claude/hooks/block_destructive_bash.py < sample-pretooluse.json
```

Add the hook to your Claude Code settings:

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

## Example blocked output

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Blocked destructive Bash command: recursive force delete with rm. Rewrite the command to be narrower, reversible, or explicitly reviewed by a human."
  }
}
```

## Log format

Each blocked command appends one line:

```text
timestamp	reason=<reason>	project=<cwd>	command=<attempted command>
```

The log path is `~/.claude/hooks/blocked.log`.

For tests, you can override the log path with `CLAUDE_HOOKS_BLOCKED_LOG`.
