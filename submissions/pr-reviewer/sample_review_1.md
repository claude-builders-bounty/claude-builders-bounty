# PR Review: docs: Add practical Pydantic v2 validator examples

**PR:** [pydantic/pydantic#12989](https://github.com/pydantic/pydantic/pull/12989)
**Reviewed:** 2026-03-29T18:45:00Z
**Model:** claude-haiku-4-5-20251001

---

## Summary
This PR adds 5 practical Pydantic v2 validator examples to the documentation, covering `field_validator`, `model_validator` (before/after), `computed_field`, and mode-based validators. The changes are purely additive — no existing docs are modified.

## Risk Assessment: Low
Documentation-only PR with no code changes; no risk to functionality.

## Identified Risks
- None identified — documentation addition only.

## Improvement Suggestions
- The `computed_field` example could mention caching behavior (`@cached_property` vs `@property`)
- Consider adding a note about validator order when multiple validators apply to the same field

## Code Quality Notes
- All examples are self-contained and runnable
- Type annotations are correct and consistent with Pydantic v2 style
- Examples cover both common and advanced use cases

## Confidence Score: High
High — small, well-scoped documentation-only change with clear, accurate examples.

## Verdict
APPROVE — Clean documentation addition with accurate, runnable examples covering key Pydantic v2 patterns.
