# Claude Code Security Hook

A production-grade `pre-tool-use` hook that blocks destructive bash commands.

## Installation

1. Copy the script to your hooks directory:
```bash
mkdir -p ~/.claude/hooks && cp hooks/pre-tool-use.sh ~/.claude/hooks/pre-tool-use.sh
```

2. Make it executable:
```bash
chmod +x ~/.claude/hooks/pre-tool-use.sh
```

## Features
- **Deterministic Blocking:** Prevents `rm -rf`, `DROP TABLE`, `git push --force`, and `TRUNCATE`.
- **Intelligent SQL Guard:** Blocks `DELETE FROM` only if a `WHERE` clause is missing.
- **Audit Logging:** Records every blocked attempt to `~/.claude/hooks/blocked.log`.
