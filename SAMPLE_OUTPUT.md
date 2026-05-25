# Sample Output: claude-review

## Test 1: PR #2087 — Pre-tool-use Hook
**Command:** `python3 claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2087`

## 🔍 PR Review Report

**PR:** [BOUNTY $100] HOOK: Pre-tool-use hook that blocks destructive bash commands
**Author:** @cendd
**Scope:** 3 files | +117/-36 lines

### 📋 Summary of Changes
This PR modifies **3 files** with **+117/-36 lines**. Implements a Claude Code pre-tool-use hook that intercepts and blocks dangerous bash commands.

**Modified files:**
- `README.md` (+27/-36)
- `pre-tool-use.sh` (+40/-0)
- `SAMPLE_OUTPUT.md` (+50/-0)

### ⚠️ Identified Risks
✅ No critical risks detected. The changes are well-contained.

### 💡 Improvement Suggestions
- Consider adding test examples for each blocked pattern

### 🎯 Confidence Score
**High**

---

## Test 2: PR #2080 — Claude PR Review Agent
**Command:** `python3 claude-review.py --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2080`

## 🔍 PR Review Report

**PR:** feat: Add Claude PR Review Agent — bounty #4
**Author:** @Hobie1Kenobi
**Scope:** 7 files | +431/-1 lines

### 📋 Summary of Changes
This PR modifies **7 files** with **+431/-1 lines**. Implements a PR Review Agent with CLI tool, GitHub Action, sample outputs, and documentation.

**Modified files:**
- `README.md` (+9/-1)
- `agents/pr-review/claude-review.py` (+98/-0)
- `agents/pr-review/claude_review_agent.py` (+248/-0)
- `agents/pr-review/SAMPLE_OUTPUT.md` (+2/-0)
- `.github/workflows/pr-review.yml` (+19/-0)
- `agents/pr-review/requirements.txt` (+21/-0)
- `agents/pr-review/README.md` (+34/-0)

### ⚠️ Identified Risks
- GitHub token usage documented — ensure tokens are never committed
- Uses ANTHROPIC_API_KEY — requires proper secret management

### 💡 Improvement Suggestions
- Large PR (431 additions) — consider splitting implementation and docs
- Consider adding unit tests for the analysis functions

### 🎯 Confidence Score
**Medium**
- Moderate size, but well-structured with documentation
