# Pre-Tool-Use Hook: Block Destructive Bash Commands

A safety hook for **Claude Code** that intercepts and blocks catastrophic shell and database commands before execution.

## Features
- **Blocks Destructive Filesystem Deletions:** Intercepts 
m -rf, 
m -fr, and split-flag variations (
m -r -f).
- **Blocks Destructive SQL Mutations:** Blocks DROP TABLE, TRUNCATE, and unbounded DELETE FROM statements lacking a WHERE clause.
- **Blocks Git History Rewrites:** Blocks git push --force and git push -f.
- **Audit Logging:** Every blocked command is logged with timestamp, project directory, and rationale to ~/.claude/hooks/blocked.log.
- **Zero False Positives:** Safe operations (
m file.txt, git push origin main, SELECT * FROM users, DELETE FROM users WHERE id = 1) pass without interference.

---

## Installation (2 commands or fewer)

`ash
mkdir -p ~/.claude/hooks && curl -sSL https://raw.githubusercontent.com/claude-builders-bounty/claude-builders-bounty/main/hooks/block_destructive_commands.py -o ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
`

Or for local installation:
`ash
mkdir -p ~/.claude/hooks && cp block_destructive_commands.py ~/.claude/hooks/pre-tool-use && chmod +x ~/.claude/hooks/pre-tool-use
`

---

## Verification & Testing

Run the included test suite:
`ash
python -m unittest tests/test_block_destructive_commands.py
`
