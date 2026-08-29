 # Destructive Command Blocker Hook
 
 A Claude Code `pre-tool-use` hook that intercepts and blocks dangerous bash commands before execution.
 
 ## Installation
 
 ```bash
 cp hooks/block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
 ```
 
 ## Blocked Patterns
 
 - `rm -rf` (recursive force delete)
 - `DROP TABLE` (SQL)
 - `git push --force` / `git push -f`
 - `TRUNCATE` (SQL)
 - `DELETE FROM <table>` without a WHERE clause
 
 ## Logging
 
 Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with timestamp, project path, reason, and the attempted command.
 
 ## Behavior
 
 - Safe commands pass through unaffected.
 - Blocked commands return a structured JSON rejection with a clear explanation.
 - The hook reads tool input from stdin as per Claude Code hooks specification.
