## Summary
This PR updates Misc/NEWS.d/next/Core_and_Builtins/2026-05-11-15-58-23.gh-issue-149689.9Ht49z.rst, Parser/action_helpers.c. The visible diff adds 51 lines and removes 15 lines, so the main review focus should be correctness, regression coverage, and maintainability of the touched files.

## Identified risks
- The diff contains credential-related terms; verify no secrets or tokens are committed.
- No obvious test files are visible in the diff, so regression coverage may be incomplete.

## Improvement suggestions
- Run the repository's automated test and lint commands before merge.
- Add or update documentation if the change affects user-facing behavior.
- Ask for focused review on the highest-risk files touched by this PR.

## Confidence
Medium — based on diff metadata and lightweight static checks.
