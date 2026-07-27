# Pre-Tool-Use Safety Hook for Claude Code

Blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp pre_tool_use_hook.py ~/.claude/hooks/pre_tool_use && chmod +x ~/.claude/hooks/pre_tool_use
```

## Blocked Patterns

| Pattern | Reason |
|---------|--------|
| rm -rf | Recursive force delete |
| git push --force to main/master | Force push to protected branch |
| DROP TABLE / DROP DATABASE | Database destruction |
| TRUNCATE TABLE | Table wipe |
| DELETE FROM without WHERE | Mass data deletion |
| chmod 777 | World-writable permissions |
| dd to /dev/sd* | Block device overwrite |
| Filesystem format commands | Formatting prevention |
| Fork bombs | System DoS |

## Warned Patterns (allowed but logged)

- git push --force to non-main branches
- sudo rm
- curl ... | sh / wget ... | sh

## Log File

Blocked attempts are logged to ~/.claude/hooks/blocked.log in JSONL format with timestamp, command, pattern, and action fields.

## Disabling Temporarily

```bash
mv ~/.claude/hooks/pre_tool_use ~/.claude/hooks/pre_tool_use.disabled
```
