## Summary

This PR adds a `pdip` footprint function as an alias for `dip` with PDIP (Plastic Dual Inline Package) defaults (300mil width, 2.54mm pitch). It re-exports the existing `dip` function with default parameters, adds the export to the index, updates the `Footprinter` type, and includes test coverage for `pdip8`, `pdip14`, and custom width configurations.

## Identified Risks

- `pdip_def` extends the zod schema with `fn: z.string()` but the `pdip` function never uses or validates against this schema — the schema is defined but unused
- The `pdip` function signature accepts `w: number` but the string parser may pass string units (e.g., `"300mil"`) — potential type mismatch if called programmatically with numeric width
- No snapshot test for `pdip14` with custom width — only `pdip8_w7.62mm` is tested with custom width

## Improvement Suggestions

- Remove the unused `pdip_def` schema or use it for validation in the `pdip` function
- Add a test for `pdip14_w7.62mm` to verify custom width works with different pin counts
- Consider adding a JSDoc comment to the `pdip` function explaining the PDIP defaults

## Confidence Score

**High** — The change is a straightforward alias with good test coverage and minimal surface area.
