# PR Review

## Summary
- This PR touches 4 file(s) with roughly 344 additions and 0 deletions.
- The primary change appears to be: Add pre-tool-use hook to block destructive bash commands.
- Author context: ## Summary

## Risks
- Force-push related logic appears in the diff and can have destructive side effects if mis-scoped.
- Database-destructive operations appear in the diff and need careful rollback and scoping checks.

## Improvement Suggestions
- Add an explicit guard or confirmation path around force-push behavior.
- Add a migration safety note or tests covering destructive query paths.

## Confidence
Medium
