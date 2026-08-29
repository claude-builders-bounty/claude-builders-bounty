 # Pre-Tool-Use Hook: Block Destructive Commands
 
 A Claude Code hook that intercepts and blocks dangerous bash commands before execution.
 
 ## Installation (2 commands)
 
 ```bash
 mkdir -p ~/.claude/hooks
 cp hooks/pre-tool-use-block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/pre-tool-use-block-destructive.sh
 ```
 
 ## Blocked Patterns
 
 | Pattern | Reason |
 |---------|--------|
 | `rm -rf` | Prevents accidental recursive file deletion |
 | `DROP TABLE` | Destructive SQL; use migrations instead |
 | `git push --force` | Can overwrite remote history irreversibly |
 | `TRUNCATE` | Destructive SQL; use DELETE with WHERE or migrations |
 | `DELETE FROM` without `WHERE` | Would delete all rows from a table |
 
 ## Logging
 
 Every blocked attempt is logged to `~/.claude/hooks/blocked.log` with:
 - UTC timestamp
 - Project path
 - Attempted command
 
 Example log entry:
 ```
 2026-08-29T12:55:00Z | /home/user/myproject | rm -rf node_modules
 ```
 
 ## How It Works
 
 1. Claude Code invokes this hook before executing any BashTool command
 2. The hook reads the command from stdin (JSON payload)
 3. If the command matches a blocked pattern, it returns `{"decision":"block","reason":"..."}`
 4. Otherwise, it returns `{"decision":"allow"}`
 5. Normal bash commands pass through unaffected
 
 ## Testing
 
 After installation, try running a blocked command in Claude Code:
 ```
 rm -rf /tmp/test
 ```
 You should see the block reason displayed, and the command will not execute.
