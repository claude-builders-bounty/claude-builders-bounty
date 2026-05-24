# Pre-Tool-Use Security Hook

Blocks destructive bash commands before they are executed by Claude Code.

## Installation (2 commands)



## What It Blocks

-  — destructive file deletion
-  — database table deletion
-  — history overwrite
-  — table truncation
-  without  — mass row deletion

## How It Works

The hook intercepts every bash tool call from Claude Code, checks the command against a list of dangerous patterns, and either allows it or replaces it with a safe blocked message.

## Logs

Blocked attempts are logged to  with:
- Timestamp
- Project path
- Attempted command
- Block reason
