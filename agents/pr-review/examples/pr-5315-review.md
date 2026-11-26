## 🤖 Claude Code Review

> **PR**: [https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5315](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/5315)
> **Title**: feat: add pre-tool-use hook to block destructive bash commands (#3)
> **Author**: @HGG-Y

### 📋 Summary

This PR changes 6 file(s) (+773/-0 lines) — “feat: add pre-tool-use hook to block destructive bash commands (#3)”, by @HGG-Y. The change touches mainly JSON, Markdown, Python, Shell; including 1 test file(s). Key files: hooks/README.md, hooks/block-destructive-commands.py, hooks/block-destructive-commands.sh. (and 3 more)

### ⚠️ Identified Risks

- No high- or medium-severity risks found by the heuristic checks.

### 💡 Improvement Suggestions

- Consider splitting this PR (773 added lines across 6 files) — smaller PRs are faster and safer to review.

### ✅ Confidence: Medium

Confidence is in *this review*, not in the PR: High means the diff was small, test-covered and fully readable; Medium / Low mean the diff was large, untested, or partly unreadable, so a human should read it more carefully.

### 📁 Files changed

| File | + | - |
| --- | ---: | ---: |
| `hooks/README.md` | 112 | 0 |
| `hooks/block-destructive-commands.py` | 349 | 0 |
| `hooks/block-destructive-commands.sh` | 23 | 0 |
| `install.sh` | 32 | 0 |
| `settings.example.json` | 1 | 0 |
| `tests/test_block_destructive_commands.py` | 256 | 0 |

_Heuristic review only — no LLM was called, no token was used, and no comment was posted by this tool unless `--post` was given. Please read the diff yourself before merging._
