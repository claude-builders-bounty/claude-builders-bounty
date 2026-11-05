## Claude Code PR Review Agent — Sample Output 1

> Generated: 2025-11-05 22:00 · Confidence: **🟡 Medium**

### Summary

alice 提交了 *feat: add webhook handler for Stripe*。本次变更涉及 **6 个文件** (+245/-32)，主要语言 .py。文件分布: .py ×4, .json ×1, .md ×1。

### Identified Risks

- ⚠️ **hardcoded-secret** found in `webhook/handler.py`
- ⚠️ **catch-all-except** found in `webhook/handler.py`

### Improvement Suggestions

- 💡 PR >300 lines — consider splitting webhook handler from Stripe-specific code
- 💡 New file `webhook/handler.py` has no tests — add coverage

### Confidence: **🟡 Medium**
