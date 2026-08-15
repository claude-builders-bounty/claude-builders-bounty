# Claude Code Pre-Tool-Use Guard Hook

Security hook for Claude Code to intercept and block destructive bash commands (`rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unbounded `DELETE`).

## Installation (2 Commands)

```bash
mkdir -p ~/.claude/hooks && cp .claude/hooks/pre-tool-use.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-tool-use.py

