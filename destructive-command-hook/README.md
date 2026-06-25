# Destructive Command PreToolUse Hook

A Claude Code `PreToolUse` hook that inspects Bash commands before execution, blocks destructive patterns, and logs every blocked attempt to `~/.claude/hooks/blocked.log`.

## What It Blocks

- `rm -rf`
- `DROP TABLE`
- `git push --force` and `git push -f`
- `TRUNCATE`
- `DELETE FROM` statements without a `WHERE` clause

Normal commands exit with code 0 and are left untouched. Blocked commands exit with code 2, print a clear reason for Claude, and append timestamp, attempted command, and project path to the blocked log.

## Install

From the repository root:

```bash
mkdir -p ~/.claude/hooks && cp destructive-command-hook/pre_tool_use_blocker.py ~/.claude/hooks/pre_tool_use_blocker.py && chmod +x ~/.claude/hooks/pre_tool_use_blocker.py
python ~/.claude/hooks/pre_tool_use_blocker.py --self-test
```

Add this hook entry to your Claude Code settings:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python ~/.claude/hooks/pre_tool_use_blocker.py"
          }
        ]
      }
    ]
  }
}
```

## Self-Test Output

```text
Self-test passed: destructive patterns blocked, normal commands allowed.
```

## Example Blocked Message

```text
Claude Code safety hook blocked this Bash command. Blocked pattern: rm -rf. Recursive forced deletion can remove project or system files. Project: /path/to/project. Attempt logged to ~/.claude/hooks/blocked.log.
```

## Log Format

Each blocked attempt is appended as one tab-separated line:

```text
2026-06-25T19:45:00+00:00    project=/repo    reason=Blocked pattern: rm -rf...    command=rm -rf dist
```
