# Claude Code Pre-Tool-Use Security Hook

A Python hook that intercepts and blocks dangerous commands (`rm -rf`, `DROP TABLE`, `TRUNCATE`, `git push --force`, `DELETE FROM` without `WHERE`) before Claude Code executes them.

## Installation

Run these two commands in your terminal:

```bash
mkdir -p ~/.claude/hooks
cp pre-tool-use.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Features
- Inspects the exact command Claude Code attempts to run.
- Returns a non-zero exit code to halt execution if a dangerous pattern is detected.
- Directly prints a clear error message back to Claude explaining why it was blocked.
- Silently logs all blocked attempts to `~/.claude/hooks/blocked.log` with a timestamp and the working directory.