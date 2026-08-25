<!-- claude-review of pallets/click#3782 -->
<!-- https://github.com/pallets/click/pull/3782 · diff: 142 lines, 3 files -->

## Summary
Stops usage-line wrapping from breaking arguments at internal hyphens: `wrap_text`
gains a `break_on_hyphens` parameter forwarded to `textwrap.TextWrapper`, and
`HelpFormatter.write_usage` passes `break_on_hyphens=False` in both its layout
branches, so long option names/metavars move whole to the next line. Ships a
CHANGES.md entry and three targeted tests reproducing issue #3362.

## Risks
- Default `break_on_hyphens=True` preserves old public behavior for direct `wrap_text` callers; only usage lines change — low regression surface.
- Usage lines with a single token wider than the terminal width will now overflow the line instead of being split (inherent trade-off; worth documenting).
- Tests assert exact wrapped output at fixed widths (20/31/65), which couples them to `textwrap` internals across Python versions — potential cross-version brittleness.
- The `not line.endswith("-")` assertions could mask legitimate trailing-hyphen text, though unlikely in usage strings.

## Suggestions
- Consider surfacing `break_on_hyphens` on the `HelpFormatter` constructor so applications can opt into the old splitting behavior without subclassing.
- Add one test asserting an over-wide single token still renders (even if it overflows) rather than raising, to pin the documented trade-off.
- The docstring `.. versionchanged:: 8.5.0` blocks assume this lands in 8.5.0 — verify against the release in CHANGES.md ("Unreleased" today).

## Confidence
High — focused fix, both write_usage branches covered, tests mirror the reported failure mode precisely.
