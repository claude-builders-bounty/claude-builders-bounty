# Claude Code pre-tool-use Destructive Command Block Hook

A safety hook that intercepts and blocks dangerous, destructive shell commands (like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and unconstrained `DELETE FROM`) before they can be executed by Claude Code.

## 🚀 Installation & Setup (2 commands)

1. **Create the Claude hooks directory and download the hook**:
   ```bash
   mkdir -p ~/.claude/hooks
   ```
2. **Move the hook script and make it executable**:
   ```bash
   mv block-destructive.sh ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
   ```

## Log Location
All blocked attempts are logged to:
`~/.claude/hooks/blocked.log`
