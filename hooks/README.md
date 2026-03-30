# Pre-Tool-Use Hook: Block Destructive Bash Commands

## Installation

```bash
mkdir -p ~/.claude/hooks
cp hooks/pre-tool-use-block-dangerous.py ~/.claude/hooks/
```

## Blocked Patterns
- rm -rf / rm -fr (recursive force delete)
- DROP TABLE (SQL)
- TRUNCATE (SQL)
- DELETE FROM without WHERE clause
- git push --force / git push -f
- Fork bombs
- Direct disk writes (> /dev/sdX)

## How It Works
1. Claude Code sends tool invocation via stdin (hooks protocol)
2. Hook checks command against blocked regex patterns
3. Match: logs to ~/.claude/hooks/blocked.log, returns reject decision
4. No match: exits 0, command proceeds

## Log Format
```timestamp | project_path | pattern | command```

## Testing
```bash
echo '{"tool_name":"bash","tool_input":{"command":"rm -rf /"},"project_path":"/test"}' | python3 hooks/pre-tool-use-block-dangerous.py
echo True
# Should output reject JSON and exit code 2
```

## License
MIT
