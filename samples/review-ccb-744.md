# Code Review: claude-builders-bounty/claude-builders-bounty#744

**PR Title:** CHANGELOG generator from git history (#1)
**URL:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/744
**Reviewer:** Claude Code (claude-sonnet-4-6)
**Date:** 2026-05-06

---

### Summary

This PR adds a bash script and README that generates a structured `CHANGELOG.md` from git history. It categorizes commits since the last tag into Added/Fixed/Changed/Removed sections using conventional commit prefix matching. The tool doubles as a standalone script and a Claude Code skill.

### Identified Risks

- **Commit message dependency:** The categorization relies entirely on conventional commit prefixes (feat, fix, etc.). Repos without consistent commit conventions will dump everything into "Changed," reducing the tool's usefulness. Document this limitation clearly.
- **Tag fallback behavior:** Falling back to the first commit when no tags exist means repos with long histories will generate an unbounded changelog. Consider adding a `--since` or `--count` flag to cap the output.
- No significant security or performance risks. The script runs locally and only reads git history.

### Improvement Suggestions

- Add a `--dry-run` flag to preview the changelog before writing to disk.
- Support a `--tag` flag to generate changelog between two specific tags (e.g., `--tag v1.0.0..v1.1.0`).
- The Claude Code skill setup instructions could be simplified — consider generating the SKILL.md automatically if `.claude/` exists.
- Add an example of the full generated CHANGELOG.md in the README (not just the header template).

### Confidence Score

**Score:** Medium

The script is simple and functional, but untested on repos with large histories (1000+ commits) or divergent commit conventions. The core logic is sound but the tag-backstop edge case warrants a guard.
