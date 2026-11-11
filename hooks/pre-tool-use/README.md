# Claude Code Pre-Tool-Use Hook: Destructive Bash Command Blocker

Guards Claude Code execution by intercepting and rejecting destructive shell commands before they execute.

## Features
- **Blocks Dangerous Patterns**:
  - `rm -rf` / `rm -fr` / `rm -r -f`
  - `DROP TABLE`
  - `git push --force` / `git push -f`
  - `TRUNCATE` / `TRUNCATE TABLE`
  - `DELETE FROM` without a `WHERE` clause
- **Audit Logging**: Logs timestamp (ISO 8601 UTC), attempted command, and working directory to `~/.claude/hooks/blocked.log`.
- **Zero Interruption**: Transparently permits safe commands (`ls`, `git status`, `npm test`, standard `rm`).
- **Dual Implementation**: High-precision Python 3 engine and zero-dependency POSIX bash script.

## 2-Command Quick Install

```bash
mkdir -p ~/.claude/hooks/pre-tool-use && cp hooks/pre-tool-use/block_destructive.py ~/.claude/hooks/pre-tool-use/
chmod +x ~/.claude/hooks/pre-tool-use/block_destructive.py
```
