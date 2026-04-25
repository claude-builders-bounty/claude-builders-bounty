# DangerShield - Pre-tool-use Hook for Claude Code

A security hook that intercepts and blocks dangerous bash commands before they execute.

## What It Blocks

- `rm -rf` — Recursive force removal
- `DROP TABLE` — Database table deletion
- `git push --force` — Git history rewrite
- `TRUNCATE` — Table data deletion
- `DELETE FROM` without `WHERE` clause — Unconditional data deletion

## Installation (2 commands)

```bash
# Download the hook
curl -fsSL https://raw.githubusercontent.com/YOUR_REPO/main/pre-tool-use -o ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

Or copy manually:
```bash
cp pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## Verification

Test it:
```bash
echo '{"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}}' | ~/.claude/hooks/pre-tool-use
# Should print blocking message and exit 1
```

## Logs

All blocked attempts are logged to:
```
~/.claude/hooks/blocked.log
```

Format: `[timestamp] BLOCKED | Project: /path | Reason: description | Command: ...`

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```
