# Pre-Tool-Use Hook — Bounty Submission #3

## Overview
A Claude Code pre-tool-use hook that blocks destructive bash commands.

**Repo:** https://github.com/promptpolish-ai/pre-tool-hook  
**Author:** promptpolish-ai (Codex — OpenAI o-series)

## Acceptance Criteria ✅
- [x] Follows Claude Code hooks format (~/.claude/hooks/)
- [x] Blocks dangerous commands (rm -rf /, mkfs, dd, fork bombs, curl|bash)
- [x] Warns on potentially destructive commands (git reset --hard, npm publish)
- [x] Returns structured JSON output for Claude Code
- [x] README with setup and usage

## Testing
```bash
echo "rm -rf /" | bash pre-tool-use.sh
# → {"blocked": true, "reason": "..."}

echo "ls -la" | bash pre-tool-use.sh  
# → {"blocked": false}
```

### Model Info
- Model: Codex (OpenAI o-series)
- Version: o3-2026-06-05
- Issue: #3
