# Test Outputs

This directory contains sample outputs from running `claude-review` on real GitHub PRs.

## Test Run 1: PR #572 (CHANGELOG generator)

**Command:** `claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/572`

**Result:**

```
## 📋 PR Review Summary

**PR:** [add: CHANGELOG generator script](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/572)
**Author:** @armorbreak001 | **State:** OPEN
**Stats:** +113 / -0 | **Files:** 1
**Languages:** Shell
**Reviewed:** 2026-04-14 10:54 UTC

### 📝 Summary
Identified 1 Medium(s) across 113 lines of new code. Affects 1 file(s) spanning Shell.
Overall confidence: 🟡 **Medium**

### ⚠️ Identified Risks
1. **[Medium]** 🟡 `Technical Debt` — Outstanding TODO/FIXME marker in code

### 💡 Improvement Suggestions
1. 💭 **Consider:** No test files detected in this PR.

### 📊 Confidence Score
**Medium** — Some risk patterns were found. Recommend thorough review of flagged areas before merge.
```

## Test Run 2: PR #573 (CLAUDE.md template)

**Command:** `claude-review --pr https://github.com/claude-builders-bounty/claude-builders-bounty/pull/573`

**Result:**

```
## 📋 PR Review Summary

**PR:** [add: CLAUDE.md template for Next.js 15 + SQLite SaaS](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/573)
**Author:** @armorbreak001 | **State:** OPEN
**Stats:** +219 / -0 | **Files:** 1
**Languages:** Markdown
**Reviewed:** 2026-04-14 10:54 UTC

### 📝 Summary
Identified 1 Critical, 1 High, 1 Medium, and 1 Low severity risk across 219 lines of new code.
Overall confidence: 🔴 **Low**

### ⚠️ Identified Risks
1. **[Critical]** 🔴 Cryptography — Weak random/token generation pattern
2. **[High]** 🟠 Security — Potential hardcoded credential
3. **[Medium]** 🟡 Supply Chain — Package install without audit
4. **[Low]** 🔵 Debug Code — Debug logging statement

### 💡 Improvement Suggestions
1. ⚡ **Recommended:** Critical risk(s) found. Review carefully before merging.
2. 💭 **Consider:** No test files detected in this PR.

### 📊 Confidence Score
**Low** — Multiple high-severity risks or large scope detected.
Detailed security and architecture review recommended.
```
