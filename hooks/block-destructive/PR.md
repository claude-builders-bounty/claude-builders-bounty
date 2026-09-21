## Fixes #3

Claude Code `PreToolUse` hook (Python, stdlib) that blocks destructive Bash before execution.

### Deliverables
- `hooks/block-destructive/block_destructive.py`
- `hooks/block-destructive/settings.json` (+ project variant)
- `hooks/block-destructive/install.sh` (2-command install)
- `hooks/block-destructive/README.md`
- `hooks/block-destructive/tests/test_patterns.py`
- `hooks/block-destructive/examples/blocked.log.sample`

### Install
```bash
curl -fsSL https://raw.githubusercontent.com/masaki12214/claude-builders-bounty/feat/block-destructive-hook-masaki/hooks/block-destructive/install.sh -o /tmp/bd-install.sh
bash /tmp/bd-install.sh
```
