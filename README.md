# Pre-Tool-Use Hook: Block Destructive Commands

Blocks dangerous bash commands before they execute in Claude Code.

## Installation (2 commands)

\\ash
# 1. Clone this repo
git clone https://github.com/Zhiyilang074811/claude-builders-bounty.git

# 2. Copy hook to Claude hooks directory
cp hooks/block-destructive.sh ~/.claude/hooks/block-destructive.sh
chmod +x ~/.claude/hooks/block-destructive.sh
\
## Blocked Patterns

- m -rf /\ — destructive filesystem removal
- \DROP TABLE\ — SQL table deletion
- \git push --force\ — force push (data loss risk)
- \TRUNCATE\ — SQL table truncation
- \DELETE FROM table\ without WHERE — mass data deletion

## How It Works

The hook reads Claude Code pre-tool-use input from stdin, checks the command against block patterns, logs blocked attempts to \~/.claude/hooks/blocked.log\, and exits with error code 1 to prevent execution.

## Tested On

- Claude Code CLI
- Windows WSL2 + macOS
