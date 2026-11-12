# PR Review — [Close contexts created during shell completion #2644](https://github.com/pallets/click/pull/2800)

## Summary
The change ensures Click contexts created during shell completion are closed, preventing resource warnings from file-backed parameters. It updates the completion context lifecycle and adds a regression test that checks warnings are not emitted.

## Risks
- No configured high-signal risk patterns were detected in added lines. This does not guarantee the change is safe.

## Suggestions
- Confirm CI covers shell completion across supported command/group modes and context-manager nesting.

## Confidence
**High** — The change is focused, includes a test-path update, and the inspected diff shows no configured high-signal patterns. Human review is still required.

_Generated from the public PR diff by the Sovereign PR Review sample workflow._
