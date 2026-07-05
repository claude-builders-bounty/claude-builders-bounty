# Pre-tool-use Hook: Block Dangerous Bash Commands

Blocks dangerous commands like `rm -rf`, `DROP TABLE`, `git push --force`, `TRUNCATE`, and `DELETE FROM` without `WHERE`.

## Installation

1. Create the hooks directory (if it doesn't exist):
```bash
mkdir -p ~/.claude/hooks
```

2. Download and install the hook:
```bash
curl -L https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/pre-tool-use -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
```

## Usage

The hook runs automatically before each bash command in Claude Code. Blocked attempts are logged to `~/.claude/hooks/blocked.log`.
