# Claude Code Protect Hook

A pre-tool-use hook that blocks destructive bash commands before they execute.

## Features

- Blocks rm -rf on sensitive directories (/, $ HOME, /tmp, etc.)
- Blocks dangerous SQL commands: DROP TABLE, DROP DATABASE, TRUNCATE
- Blocks git push --force to prevent history overwriting
- Blocks dd and direct device writes
- Logs all blocked attempts to $ HOME/.claude/hooks/blocked.log

## Installation

1. mkdir -p $ HOME/.claude/hooks
2. cp pre-tool-use.py $ HOME/.claude/hooks/

## Requirements

- Python 3.6+
- Claude Code

## License

MIT
