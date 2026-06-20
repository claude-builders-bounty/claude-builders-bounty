# Destructive Command Blocker Hook

A Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands before they execute.

## Installation (2 commands)

```bash
mkdir -p ~/.claude/hooks && curl -sL https://raw.githubusercontent.com/YOUR_USER/claude-builders-bounty/main/hooks/destructive-command-blocker/pre-bash-firewall.sh -o ~/.claude/hooks/pre-bash-firewall.sh && chmod +x ~/.claude/hooks/pre-bash-firewall.sh
```

Then add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/pre-bash-firewall.sh"
          }
        ]
      }
    ]
  }
}
```

## Blocked Patterns

| Pattern | What it catches |
|---------|----------------|
| `rm -rf /` | Recursive force delete root |
| `rm -rf ~` | Recursive force delete home |
| `rm -rf *` | Recursive force delete all |
| `rm -rf .` | Recursive force delete current dir |
| `DROP TABLE` | SQL table deletion |
| `DROP DATABASE` | SQL database deletion |
| `TRUNCATE` | SQL table truncation |
| `DELETE FROM` (no WHERE) | SQL mass deletion |
| `DELETE FROM WHERE 1=1` | SQL mass deletion |
| `git push --force` | Force push (allows --force-with-lease) |
| `git reset --hard` | Hard reset |
| `git clean -f` | Force clean |
| `sudo rm` | Sudo remove |
| `chmod -R 777` | Overly permissive chmod |
| `curl \| bash` | Pipe to bash |
| `wget \| bash` | Pipe to bash |
| Fork bomb | `:(){ :|:& };:` |

## Logging

All blocked attempts are logged to `~/.claude/hooks/blocked.log` with:

- Timestamp (UTC ISO 8601)
- Matched pattern
- Attempted command
- Project path

## How it works

1. Receives JSON from Claude Code on stdin
2. Checks if the tool is Bash
3. Extracts the command string
4. Tests against known destructive patterns
5. Blocks with explanation if matched, allows if not
6. Logs all blocked attempts

## Exit codes

- `0` — Command allowed (or not a Bash tool)
- Block decision returned as JSON with `{"decision":"block","reason":"..."}`

## Customization

Edit the `DENY_PATTERNS` array in the script to add or remove patterns.
