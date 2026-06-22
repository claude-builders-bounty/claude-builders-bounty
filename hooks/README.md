# 🛡️ Destructive Command Blocker Hook

Blocks dangerous bash commands before execution in Claude Code.

**Two versions:** Bash (`pre-tool-use`) & Python (`block_destructive_bash.py`)

## Install
```bash
mkdir -p ~/.claude/hooks
# Bash
curl -o ~/.claude/hooks/pre-tool-use https://raw.githubusercontent.com/fanjuxin9630/claude-builders-bounty/bounty-3-hook/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
# Python
curl -o ~/.claude/hooks/block_destructive_bash.py https://raw.githubusercontent.com/fanjuxin9630/claude-builders-bounty/bounty-3-hook/hooks/block_destructive_bash.py
chmod +x ~/.claude/hooks/block_destructive_bash.py
```
