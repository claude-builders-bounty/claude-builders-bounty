# Claude Code destructive Bash guard

A `PreToolUse` hook that blocks dangerous Bash commands before Claude Code can run them.

## Install (2 commands)

1. Copy the hook into your Claude Code hooks directory:

   ```bash
   mkdir -p ~/.claude/hooks && cp hooks/block_destructive_bash.py ~/.claude/hooks/block_destructive_bash.py && chmod +x ~/.claude/hooks/block_destructive_bash.py
   ```

2. Add this `PreToolUse` entry to `~/.claude/settings.json`:

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

## What it blocks

The hook denies Bash tool calls that contain any of these patterns:

- `rm -rf` / `rm -fr` recursive force removal variants
- `DROP TABLE`
- `git push --force`, `git push --force-with-lease`, or `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements that do not include a `WHERE` clause

Normal commands such as `npm test`, `git push origin main`, `rm build.log`, and `DELETE FROM users WHERE id = 1` are allowed.

## Log file

Every blocked command is appended as JSON Lines to:

```text
~/.claude/hooks/blocked.log
```

Each log entry contains:

- UTC timestamp
- attempted command
- project path from the hook payload or `CLAUDE_PROJECT_DIR`
- block reason

## Test

Run the included standard-library tests:

```bash
python3 hooks/test_block_destructive_bash.py
```
