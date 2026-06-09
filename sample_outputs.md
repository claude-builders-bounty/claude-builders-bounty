# Sample Outputs

## Test 1: agno-agi/agno PR #8199

**Command:** `python claude_review.py --pr https://github.com/agno-agi/agno/pull/8199`

**Output:**

## 🔍 PR Review

**PR:** https://github.com/agno-agi/agno/pull/8199
**Author:** @zeroknowledge0x
**Changes:** 2 files, +287/-173

### 📝 Summary
PR by @zeroknowledge0x modifies 2 file(s) (+287/-173). Branch `fix/postgres-get-table-race-condition` -> `main`.

### ⚠️ Risks
- No obvious risks detected from diff analysis

### 💡 Suggestions
- New imports added — ensure no unused dependencies

### 🎯 Confidence: 🟡 Medium

---

## Test 2: Scottcjn/rustchain-bounties PR #12622

**Command:** `python claude_review.py --pr https://github.com/Scottcjn/rustchain-bounties/pull/12622`

**Output:**

## 🔍 PR Review

**PR:** https://github.com/Scottcjn/rustchain-bounties/pull/12622
**Author:** @zeroknowledge0x
**Changes:** 3 files, +4002/-0

### 📝 Summary
PR by @zeroknowledge0x modifies 3 file(s) (+4002/-0). Branch `feat/bounty-index-json` -> `main`.

### ⚠️ Risks
- Possible hardcoded credentials or secrets in code
- High addition count (4002 lines) — review complexity

### 💡 Suggestions
- Code appears clean — verify test coverage for new functionality

### 🎯 Confidence: 🟡 Medium
