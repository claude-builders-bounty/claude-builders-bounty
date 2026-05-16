# Destructive Command Blocker Hook

Claude Code `pre-tool-use` hook that blocks destructive Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks && cp destructive_command_blocker.py ~/.claude/hooks/destructive_command_blocker.py
chmod +x ~/.claude/hooks/destructive_command_blocker.py
```

Add the hook to your Claude Code settings as a `PreToolUse` hook for Bash. Copy the `hooks` block from `settings.example.json` into your Claude Code settings file.

## What it blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force`, `git push -f`, and `git push --force-with-lease`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Every blocked attempt is logged to:

```text
~/.claude/hooks/blocked.log
```

Each log line includes timestamp, project path, matched pattern, and attempted command.

## Example

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf build"},"cwd":"/tmp/project"}' \
  | ~/.claude/hooks/destructive_command_blocker.py
```

Output:

```text
Blocked destructive Bash command.
Pattern: rm -rf
Reason: Recursive force deletion with rm -rf can destroy project or system files.
Revise the command to use a safer, scoped operation before retrying.
```

Safe commands exit successfully and do not write to `blocked.log`.
