# Pre-Tool-Use Hook: Block Destructive Commands

A Claude Code hook that blocks dangerous bash commands before execution.

## Installation

1. Create `.claude/hooks/` in your project root
2. Copy `pre-tool-use.sh` there
3. Make it executable: `chmod +x .claude/hooks/pre-tool-use.sh`

## What it blocks

- `rm -rf /` and `rm -rf /*` (filesystem destruction)
- `mkfs.*` and `dd if=` (disk operations)
- `> /dev/*` (device writes)
- `chmod -R 000` (permission lockout)
- Fork bomb patterns
- Pipe-from-curl/wget to bash
- SQL injection patterns (DROP TABLE/DATABASE)
- `git reset --hard HEAD` (code loss)

## Allowed exceptions

Safe cleanup commands are allowed:
- `rm -rf node_modules`, `.next`, `dist`, `build`, `.cache`, `target`
- `git reset --hard HEAD~1` or `origin/main`

## How it works

Claude Code calls this hook before every tool use. If the tool is `bash` and the command matches a destructive pattern, it intercepts and returns a safe echo instead.
