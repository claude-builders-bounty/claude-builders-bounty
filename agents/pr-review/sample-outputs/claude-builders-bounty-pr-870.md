## Claude PR Review

**PR:** [Add Claude PR reviewer agent](https://github.com/claude-builders-bounty/claude-builders-bounty/pull/870)
**Author:** @minyanyi

### Summary
This PR, `Add Claude PR reviewer agent`, proposes changes from `fix/claude-pr-review-agent` into `main` across 9 file(s), with 482 additions and 0 deletions. The main touched paths are .gitattributes, agents/pr-reviewer/README.md, agents/pr-reviewer/claude-review, agents/pr-reviewer/claude_review.py, and 5 more.

### Identified risks
- Auth, permission, or secret-handling code appears in the diff, which raises security review importance.

### Improvement suggestions
- Check authorization boundaries, secret handling, and error messages for information leaks.
- Ask the author to confirm the exact manual or automated validation performed.

### Confidence score: High
