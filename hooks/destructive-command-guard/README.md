# Destructive Command Guard

Claude Code `pre-tool-use` hook for bounty #3.

## What it blocks

- `rm -rf`
- - `DROP TABLE`
  - - `git push --force`, `-f`, and `--force-with-lease`
    - - `TRUNCATE`
      - - `DELETE FROM` when no `WHERE` clause is present
       
        - Blocked attempts are appended to:
       
        - ```text
          ~/.claude/hooks/blocked.log
          ```

          Each log entry includes timestamp, command, project path, and matched rule.

          ## Install

          ```bash
          mkdir -p ~/.claude/hooks
          cp destructive_command_guard.py ~/.claude/hooks/
          chmod +x ~/.claude/hooks/destructive_command_guard.py
          ```

          ## Example hook config

          ```json
          {
            "hooks": {
              "pre-tool-use": [
                {
                  "matcher": "Bash",
                  "hooks": [
                    {
                      "type": "command",
                      "command": "~/.claude/hooks/destructive_command_guard.py"
                    }
                  ]
                }
              ]
            }
          }
          ```
          
