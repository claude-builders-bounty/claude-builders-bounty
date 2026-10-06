# pre-tool-use — Destructive Bash Command Blocker

Claude Code hook that intercepts dangerous commands before they execute.

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf ...` | Recursive force-delete |
| `DROP TABLE` | Permanent DB table deletion |
| `git push --force` / `-f` | Remote history overwrite |
| `TRUNCATE TABLE` | Instant full-row wipe |
| `DELETE FROM …` (no `WHERE`) | Full-table row deletion |

Every blocked attempt is logged with a timestamp, attempted command, and project path to `~/.claude/hooks/blocked.log`, and Claude receives a clear inline explanation.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp .claude/hooks/pre-tool-use ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

That's it — restart Claude Code and the hook is active.

## Uninstall

```bash
rm ~/.claude/hooks/pre-tool-use
```

## How it works

- Claude Code invokes the hook as `pre-tool-use` before every tool call.
- The hook reads the JSON payload, extracts `"command"`, normalises whitespace, and runs regex checks against the five patterns above.
- On a match it writes a block alert into Claude's thinking block (so you see it in chat), logs to `~/.claude/hooks/blocked.log`, and exits with code 1 to prevent execution.
- Any non-Bash tool call passes through silently.

## Configuration

None required. To customise the log path or add patterns, edit `~/.claude/hooks/pre-tool-use` directly.
