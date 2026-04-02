# Sample PR Reviews

This directory contains example outputs from claude-review on real GitHub PRs.

---

## Sample 1: Next.js Documentation PR

**PR:** [#92237](https://github.com/vercel/next.js/pull/92237)
**Title:** Docs/remove deprecated zod methods from forms and authentication guides
**Date:** 2026-04-02

### Review Output

```
## 🔍 Claude PR Review

**PR:** [#92237](https://github.com/vercel/next.js/pull/92237) **Docs/remove deprecated zod methods from forms and authentication guides**
**Author:** @unknown
**Files:** 2 | **+12** / **-47**

---

### Summary
This PR removes deprecated Zod validation methods from the Next.js documentation guides for forms and authentication. The changes update code examples to use the current Zod API, ensuring developers following the docs won't encounter deprecation warnings or errors when implementing form validation and auth flows.

### Identified Risks
- Documentation changes may break existing user implementations if they rely on the old API patterns
- Search engines may cache old documentation pages before the deploy

### Improvement Suggestions
- Consider adding a migration guide or codemod for users upgrading from deprecated Zod methods
- Cross-reference with Zod's official migration documentation to ensure all deprecated patterns are covered

### Confidence Score
🟢 High

---

*Reviewed by [Claude](https://claude.ai) via claude-review • [Source](https://github.com/claude-builders-bounty/claude-builders-bounty)*
```

---

## Sample 2: Turbopack Error Messages

**PR:** [#92234](https://github.com/vercel/next.js/pull/92234)
**Title:** Turbopack: Include a random sample of matched paths in error messages when TOO_MANY_MATCHES_LIMIT is exceeded
**Date:** 2026-04-02

### Review Output

```
## 🔍 Claude PR Review

**PR:** [#92234](https://github.com/vercel/next.js/pull/92234) **Turbopack: Include a random sample of matched paths in error messages when TOO_MANY_MATCHES_LIMIT is exceeded**
**Author:** @unknown
**Files:** 3 | **+89** / **-34**

---

### Summary
This PR improves Turbopack error messages by including a random sample of matched file paths when the TOO_MANY_MATCHES_LIMIT threshold is exceeded. This helps developers debugging routing issues by showing concrete examples of what paths are being matched, rather than just stating the limit was hit. The implementation uses reservoir sampling to ensure representative examples regardless of total match count.

### Identified Risks
- Random sampling adds non-determinism to error messages, which may make some CI/CD error snapshot tests flaky
- The random seed may need to be controlled for reproducible error messages in tests

### Improvement Suggestions
- Document the sampling behavior so developers understand why they see different paths in different runs
- Add a flag to disable sampling for test environments to ensure deterministic output
- Consider capping the maximum sample size even if total matches are very large

### Confidence Score
🟡 Medium

---

*Reviewed by [Claude](https://claude.ai) via claude-review • [Source](https://github.com/claude-builders-bounty/claude-builders-bounty)*
```

---

## How These Were Generated

These samples were generated using the claude-review CLI:

```bash
# Install
git clone https://github.com/claude-builders-bounty/claude-builders-bounty.git
cd claude-builders-bounty/claude-review
npm install && npm run build

# Review a PR
claude-review --pr https://github.com/vercel/next.js/pull/92237

# Review and post comment
claude-review --pr https://github.com/vercel/next.js/pull/92237 --post
```
