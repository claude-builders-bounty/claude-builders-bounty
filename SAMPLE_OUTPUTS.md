# PR Review Sample Outputs

## Sample 1: PR #1682 — Pre-tool-use hook

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1682

```
# PR Review: [BOUNTY $100] HOOK: Pre-tool-use hook that blocks dangerous bash commands

**PR:** `niufox/open` | **Files:** 2 | **+94/-40

## Summary
This PR modifies 2 files with 94 additions and 40 deletions.

## Changed Files
- README.md (+28/-40)
- pre-tool-use.py (+66/-0)

## 🔴 Identified Risks
- Bare/empty exception handler in pre-tool-use.py

## 🟡 Improvement Suggestions
- Debug output left in pre-tool-use.py

## 🟢 Positives
- Change touches only 2 files — focused scope

## Confidence Score
**Low** — Manual review recommended
```

## Sample 2: PR #1678 — Changelog generator

**PR:** https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1678

```
# PR Review: feat: generate-changelog skill

**PR:** `18060910075zx-coder/open` | **Files:** 4 | **+364/-0

## Summary
This PR adds 364 lines across 4 files implementing a changelog generator.

## Changed Files
- SKILL.md (+95/-0)
- SKILL_README.md (+68/-0)
- changelog.sh (+186/-0)
- sample_CHANGELOG.md (+15/-0)

## 🔴 Identified Risks
_No risks identified._

## 🟡 Improvement Suggestions
_None._

## 🟢 Positives
- No significant risks detected

## Confidence Score
**High**
```
